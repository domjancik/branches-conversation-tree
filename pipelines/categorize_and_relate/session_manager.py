#!/usr/bin/env python3
"""
Session Manager for Categorize & Relate Pipeline

Handles session-based artifact storage with unique run IDs to persist all 
intermediate outputs in organized directory structures.

Features:
- Unique session ID generation based on timestamp
- Session directory creation and management
- Intermediate artifact persistence (audio, transcripts, categorization, etc.)
- Session metadata tracking and cleanup
- Integration with existing pipeline flow
"""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import uuid
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages pipeline execution sessions with artifact persistence."""
    
    def __init__(self, base_dir: Union[str, Path] = None):
        """Initialize session manager.
        
        Args:
            base_dir: Base directory for session storage. Defaults to ./recordings
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / "recordings"
        self.base_dir.mkdir(exist_ok=True)
        self.current_session: Optional['PipelineSession'] = None
        
    def create_session(self, session_id: str = None) -> 'PipelineSession':
        """Create a new pipeline session.
        
        Args:
            session_id: Optional custom session ID. Generated if not provided.
            
        Returns:
            PipelineSession instance
        """
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
            
        session = PipelineSession(self.base_dir, session_id)
        self.current_session = session
        return session
        
    def get_session(self, session_id: str) -> Optional['PipelineSession']:
        """Retrieve an existing session by ID."""
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            return PipelineSession(self.base_dir, session_id)
        return None
        
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions with metadata."""
        sessions = []
        for session_dir in self.base_dir.iterdir():
            if session_dir.is_dir() and not session_dir.name.startswith('.'):
                try:
                    session = PipelineSession(self.base_dir, session_dir.name)
                    metadata = session.get_metadata()
                    sessions.append({
                        'session_id': session_dir.name,
                        'created': metadata.get('created'),
                        'status': metadata.get('status', 'unknown'),
                        'has_audio': session.has_artifact('audio'),
                        'has_transcript': session.has_artifact('transcript'),
                        'has_categorization': session.has_artifact('categorization'),
                        'artifact_count': len(session.list_artifacts())
                    })
                except Exception as e:
                    logger.warning(f"Failed to read session {session_dir.name}: {e}")
                    continue
                    
        # Sort by creation time, newest first
        sessions.sort(key=lambda x: x.get('created', ''), reverse=True)
        return sessions
        
    def cleanup_old_sessions(self, keep_count: int = 10) -> int:
        """Remove old sessions, keeping only the most recent ones.
        
        Args:
            keep_count: Number of recent sessions to keep
            
        Returns:
            Number of sessions removed
        """
        sessions = self.list_sessions()
        removed_count = 0
        
        if len(sessions) > keep_count:
            for session in sessions[keep_count:]:
                session_dir = self.base_dir / session['session_id']
                try:
                    shutil.rmtree(session_dir)
                    removed_count += 1
                    logger.info(f"Removed old session: {session['session_id']}")
                except Exception as e:
                    logger.error(f"Failed to remove session {session['session_id']}: {e}")
                    
        return removed_count


class PipelineSession:
    """Represents a single pipeline execution session with artifact storage."""
    
    def __init__(self, base_dir: Path, session_id: str):
        """Initialize pipeline session.
        
        Args:
            base_dir: Base directory for session storage
            session_id: Unique session identifier
        """
        self.base_dir = Path(base_dir)
        self.session_id = session_id
        self.session_dir = self.base_dir / session_id
        
        # Create session directory and subdirectories
        self.session_dir.mkdir(exist_ok=True)
        (self.session_dir / "artifacts").mkdir(exist_ok=True)
        (self.session_dir / "intermediate").mkdir(exist_ok=True)
        (self.session_dir / "logs").mkdir(exist_ok=True)
        
        # Initialize metadata if it doesn't exist
        self.metadata_file = self.session_dir / "session_metadata.json"
        if not self.metadata_file.exists():
            self._init_metadata()
            
    def _init_metadata(self):
        """Initialize session metadata file."""
        metadata = {
            'session_id': self.session_id,
            'created': datetime.now().isoformat(),
            'status': 'initialized',
            'pipeline_version': '1.0',
            'artifacts': {},
            'processing_steps': [],
            'error_log': []
        }
        self._save_metadata(metadata)
        
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save session metadata: {e}")
            
    def get_metadata(self) -> Dict[str, Any]:
        """Get session metadata."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read session metadata: {e}")
        
        # Return default metadata if file doesn't exist or is corrupted
        return {
            'session_id': self.session_id,
            'created': 'unknown',
            'status': 'unknown',
            'artifacts': {},
            'processing_steps': []
        }
        
    def update_status(self, status: str, details: str = None):
        """Update session status."""
        metadata = self.get_metadata()
        metadata['status'] = status
        metadata['last_updated'] = datetime.now().isoformat()
        
        if details:
            metadata['processing_steps'].append({
                'timestamp': datetime.now().isoformat(),
                'step': status,
                'details': details
            })
            
        self._save_metadata(metadata)
        
    def log_error(self, error: str, step: str = None):
        """Log an error to session metadata."""
        metadata = self.get_metadata()
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'step': step or 'unknown'
        }
        
        if 'error_log' not in metadata:
            metadata['error_log'] = []
        metadata['error_log'].append(error_entry)
        
        # Also save to log file
        log_file = self.session_dir / "logs" / "errors.log"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{error_entry['timestamp']}] {step}: {error}\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")
            
        self._save_metadata(metadata)
        
    def save_artifact(self, name: str, data: Any, artifact_type: str = 'file', 
                     metadata: Dict[str, Any] = None) -> Path:
        """Save an artifact to the session.
        
        Args:
            name: Artifact name/filename
            data: Artifact data (bytes, str, or dict for JSON)
            artifact_type: Type of artifact ('file', 'json', 'text', 'binary')
            metadata: Optional metadata about the artifact
            
        Returns:
            Path to saved artifact
        """
        artifact_dir = self.session_dir / "artifacts"
        
        if artifact_type == 'json':
            artifact_path = artifact_dir / f"{name}.json"
            with open(artifact_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        elif artifact_type == 'text':
            artifact_path = artifact_dir / f"{name}.txt"
            with open(artifact_path, 'w', encoding='utf-8') as f:
                f.write(str(data))
                
        elif artifact_type == 'binary':
            artifact_path = artifact_dir / name
            with open(artifact_path, 'wb') as f:
                f.write(data)
                
        else:  # 'file' - generic file handling
            artifact_path = artifact_dir / name
            if isinstance(data, (str, bytes)):
                mode = 'wb' if isinstance(data, bytes) else 'w'
                encoding = None if isinstance(data, bytes) else 'utf-8'
                with open(artifact_path, mode, encoding=encoding) as f:
                    f.write(data)
            else:
                # Assume it's JSON-serializable
                with open(artifact_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Update session metadata
        session_metadata = self.get_metadata()
        if 'artifacts' not in session_metadata:
            session_metadata['artifacts'] = {}
            
        session_metadata['artifacts'][name] = {
            'path': str(artifact_path.relative_to(self.session_dir)),
            'type': artifact_type,
            'created': datetime.now().isoformat(),
            'size': artifact_path.stat().st_size,
            'metadata': metadata or {}
        }
        
        self._save_metadata(session_metadata)
        logger.info(f"Saved artifact '{name}' to session {self.session_id}")
        
        return artifact_path
        
    def save_intermediate(self, step: str, name: str, data: Any, 
                         artifact_type: str = 'json') -> Path:
        """Save intermediate processing data.
        
        Args:
            step: Processing step name (e.g., 'whisper_output', 'llm_response')
            name: Artifact name
            data: Data to save
            artifact_type: Type of artifact
            
        Returns:
            Path to saved intermediate file
        """
        intermediate_dir = self.session_dir / "intermediate" / step
        intermediate_dir.mkdir(exist_ok=True)
        
        if artifact_type == 'json':
            file_path = intermediate_dir / f"{name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif artifact_type == 'text':
            file_path = intermediate_dir / f"{name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(data))
        else:
            file_path = intermediate_dir / name
            if isinstance(data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(data)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
                    
        logger.info(f"Saved intermediate '{step}/{name}' to session {self.session_id}")
        return file_path
        
    def get_artifact(self, name: str) -> Optional[Any]:
        """Retrieve an artifact by name."""
        metadata = self.get_metadata()
        artifacts = metadata.get('artifacts', {})
        
        if name not in artifacts:
            return None
            
        artifact_info = artifacts[name]
        artifact_path = self.session_dir / artifact_info['path']
        
        if not artifact_path.exists():
            return None
            
        try:
            if artifact_info['type'] == 'json':
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif artifact_info['type'] == 'text':
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif artifact_info['type'] == 'binary':
                with open(artifact_path, 'rb') as f:
                    return f.read()
            else:
                # Try to determine content type
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return content
        except Exception as e:
            logger.error(f"Failed to read artifact '{name}': {e}")
            return None
            
    def has_artifact(self, name: str) -> bool:
        """Check if an artifact exists."""
        metadata = self.get_metadata()
        artifacts = metadata.get('artifacts', {})
        return name in artifacts
        
    def list_artifacts(self) -> List[str]:
        """List all artifacts in the session."""
        metadata = self.get_metadata()
        return list(metadata.get('artifacts', {}).keys())
        
    def get_artifact_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata about an artifact."""
        metadata = self.get_metadata()
        artifacts = metadata.get('artifacts', {})
        return artifacts.get(name)
        
    def cleanup(self):
        """Clean up session directory and all artifacts."""
        try:
            shutil.rmtree(self.session_dir)
            logger.info(f"Cleaned up session {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup session {self.session_id}: {e}")
            
    def export_session(self, export_path: Union[str, Path]) -> Path:
        """Export session to a zip file or directory.
        
        Args:
            export_path: Path to export to
            
        Returns:
            Path to exported file/directory
        """
        export_path = Path(export_path)
        
        if export_path.suffix == '.zip':
            # Create zip archive
            import zipfile
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.session_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.session_dir.parent)
                        zipf.write(file_path, arcname)
        else:
            # Copy directory
            if export_path.exists():
                shutil.rmtree(export_path)
            shutil.copytree(self.session_dir, export_path)
            
        logger.info(f"Exported session {self.session_id} to {export_path}")
        return export_path
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the session."""
        metadata = self.get_metadata()
        artifacts = metadata.get('artifacts', {})
        
        return {
            'session_id': self.session_id,
            'status': metadata.get('status', 'unknown'),
            'created': metadata.get('created'),
            'last_updated': metadata.get('last_updated'),
            'artifact_count': len(artifacts),
            'artifacts': list(artifacts.keys()),
            'processing_steps': len(metadata.get('processing_steps', [])),
            'errors': len(metadata.get('error_log', [])),
            'directory_size': sum(f.stat().st_size for f in self.session_dir.rglob('*') if f.is_file())
        }


# Context manager for easy session handling
class SessionContext:
    """Context manager for pipeline sessions."""
    
    def __init__(self, session_manager: SessionManager, session_id: str = None):
        self.session_manager = session_manager
        self.session_id = session_id
        self.session: Optional[PipelineSession] = None
        
    def __enter__(self) -> PipelineSession:
        self.session = self.session_manager.create_session(self.session_id)
        self.session.update_status('started', 'Session context entered')
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                self.session.log_error(f"{exc_type.__name__}: {exc_val}", 'session_context')
                self.session.update_status('error', f'Session ended with error: {exc_val}')
            else:
                self.session.update_status('completed', 'Session completed successfully')


# Utility functions
def create_session_manager(base_dir: Union[str, Path] = None) -> SessionManager:
    """Create a session manager instance."""
    return SessionManager(base_dir)


def with_session(base_dir: Union[str, Path] = None, session_id: str = None):
    """Decorator for functions that need session management."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            session_manager = SessionManager(base_dir)
            with SessionContext(session_manager, session_id) as session:
                return func(session, *args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Demo/testing code
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        # Create demo session
        manager = SessionManager()
        
        with SessionContext(manager) as session:
            print(f"Created session: {session.session_id}")
            
            # Save some demo artifacts
            session.save_artifact('sample_audio', b'fake audio data', 'binary')
            session.save_artifact('transcript', 'This is a sample transcript', 'text')
            session.save_artifact('categorization', {
                'segments': [{'id': 'test', 'category': 'demo'}]
            }, 'json')
            
            # Save intermediate data
            session.save_intermediate('whisper', 'raw_output', {'segments': []})
            session.save_intermediate('llm', 'response', 'LLM response text')
            
            print(f"Session artifacts: {session.list_artifacts()}")
            print(f"Session summary: {session.get_summary()}")
            
        print("\nSession completed!")
        
        # List all sessions
        sessions = manager.list_sessions()
        print(f"Available sessions: {len(sessions)}")
        for session_info in sessions:
            print(f"  - {session_info['session_id']}: {session_info['status']}")
