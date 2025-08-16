require('dotenv').config();
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Database path
const DB_PATH = process.env.DATABASE_PATH || 'C:\\Users\\magne\\Documents\\Branches-ConversationTree\\Branches-ConversationTree-DB.db';
const IMAGES_DIR = process.env.IMAGES_DIRECTORY || 'C:\\Users\\magne\\Documents\\Branches-ConversationTree\\image_generations';
const AUDIO_DIR = process.env.AUDIO_DIRECTORY || 'C:\\Users\\magne\\Documents\\Branches-ConversationTree\\audio_recordings';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));
app.use('/images', express.static(IMAGES_DIR));
app.use('/audio', express.static(AUDIO_DIR));

// Database connection
const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to the SQLite database.');
  }
});

// API Routes

// Get configuration for the frontend
app.get('/api/config', (req, res) => {
  const config = {
    defaultRootIndex: parseInt(process.env.DEFAULT_ROOT_INDEX) || 0,
    initialExpandLevel: parseInt(process.env.INITIAL_EXPAND_LEVEL) || 2,
    maxNodeTextLength: parseInt(process.env.MAX_NODE_TEXT_LENGTH) || 20,
    animationDuration: parseInt(process.env.ANIMATION_DURATION) || 750,
    nodeRadius: parseInt(process.env.NODE_RADIUS) || 8,
    treeMargin: {
      top: parseInt(process.env.TREE_MARGIN_TOP) || 40,
      right: parseInt(process.env.TREE_MARGIN_RIGHT) || 40,
      bottom: parseInt(process.env.TREE_MARGIN_BOTTOM) || 40,
      left: parseInt(process.env.TREE_MARGIN_LEFT) || 40
    }
  };
  res.json(config);
});

// Get all audio recordings with their relationships
app.get('/api/recordings', (req, res) => {
  const query = `
    SELECT 
      id,
      audio_file_path,
      created_date,
      updated_date,
      transcription,
      parent_audio_recording_id,
      parent_time,
      duration
    FROM audio_recordings
    ORDER BY id
  `;
  
  db.all(query, [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// Get recording tree data formatted for D3.js
app.get('/api/tree-data', (req, res) => {
  const query = `
    SELECT 
      id,
      audio_file_path,
      created_date,
      transcription,
      parent_audio_recording_id,
      parent_time,
      duration
    FROM audio_recordings
    ORDER BY id
  `;
  
  db.all(query, [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    
    // Build tree structure
    const recordingsMap = {};
    const roots = [];
    
    // First pass: create all nodes
    rows.forEach(row => {
      recordingsMap[row.id] = {
        id: row.id,
        name: path.basename(row.audio_file_path, path.extname(row.audio_file_path)),
        fullPath: row.audio_file_path,
        transcription: row.transcription || '',
        transcriptionPreview: row.transcription ? row.transcription.substring(0, 100) + '...' : '',
        parentId: row.parent_audio_recording_id,
        parentTime: row.parent_time,
        duration: row.duration,
        createdDate: row.created_date,
        children: []
      };
    });
    
    // Second pass: build relationships
    Object.values(recordingsMap).forEach(node => {
      if (node.parentId && recordingsMap[node.parentId]) {
        recordingsMap[node.parentId].children.push(node);
      } else {
        roots.push(node);
      }
    });
    
    res.json({ roots, allNodes: recordingsMap });
  });
});

// Get images for a specific recording
app.get('/api/recordings/:id/images', (req, res) => {
  const recordingId = req.params.id;
  const query = `
    SELECT 
      id,
      image_file_path,
      prompt,
      reason,
      seed,
      created_date,
      status
    FROM recording_image_generations
    WHERE audio_recording_id = ?
    ORDER BY created_date
  `;
  
  db.all(query, [recordingId], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// Get all images with their recording relationships
app.get('/api/images', (req, res) => {
  const query = `
    SELECT 
      rig.id,
      rig.audio_recording_id,
      rig.image_file_path,
      rig.prompt,
      rig.reason,
      rig.seed,
      rig.created_date,
      rig.status,
      ar.audio_file_path as recording_path
    FROM recording_image_generations rig
    JOIN audio_recordings ar ON rig.audio_recording_id = ar.id
    ORDER BY rig.created_date
  `;
  
  db.all(query, [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// Serve static files and fallback to index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Closing database connection...');
  db.close((err) => {
    if (err) {
      console.error(err.message);
    }
    console.log('Database connection closed.');
    process.exit(0);
  });
});
