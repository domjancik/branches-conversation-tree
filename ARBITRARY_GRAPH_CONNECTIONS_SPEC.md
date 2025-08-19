# Arbitrary Graph Connections Extension Specification

## Overview

This specification extends the branches-conversation-tree system to support arbitrary graph connections beyond the traditional hierarchical parent-child relationships. This enables rich, non-linear storytelling patterns and complex relationship modeling between conversation nodes, images, and generated content.

## Core Concepts

### Beyond Tree Hierarchy

While the core system maintains a tree structure for conversation flow, this extension adds the capability to create arbitrary connections that represent:
- **Thematic Links**: Content with similar themes or topics
- **Character Continuity**: References to the same characters across branches  
- **Temporal Relationships**: Past/future references, flashbacks, foreshadowing
- **Causal Connections**: Cause and effect relationships across different branches
- **Semantic Similarity**: Content with similar meaning or context
- **Visual Continuity**: Images with similar style, color palette, or composition
- **Narrative Threads**: Story arcs that span multiple branches
- **Meta-References**: Self-referential or recursive storytelling elements

### Graph vs Tree Coexistence

The system maintains **both** structures simultaneously:
- **Tree Structure**: Primary navigation and hierarchical organization
- **Graph Structure**: Rich interconnections and relationship modeling
- **Hybrid Views**: Visualizations that can show both or switch between them

## Data Model Extensions

### Connection Types

```typescript
enum ConnectionType {
  // Semantic Connections
  THEMATIC_LINK = 'thematic_link',
  SEMANTIC_SIMILARITY = 'semantic_similarity',
  TOPIC_REFERENCE = 'topic_reference',
  
  // Narrative Connections
  CHARACTER_CONTINUITY = 'character_continuity',
  STORY_ARC = 'story_arc',
  PLOT_THREAD = 'plot_thread',
  
  // Temporal Connections
  FLASHBACK = 'flashback',
  FORESHADOWING = 'foreshadowing',
  TEMPORAL_REFERENCE = 'temporal_reference',
  
  // Causal Connections
  CAUSES = 'causes',
  RESULTS_FROM = 'results_from',
  INFLUENCES = 'influences',
  
  // Visual Connections
  VISUAL_SIMILARITY = 'visual_similarity',
  STYLE_CONTINUITY = 'style_continuity',
  COLOR_HARMONY = 'color_harmony',
  COMPOSITION_ECHO = 'composition_echo',
  
  // Meta Connections
  SELF_REFERENCE = 'self_reference',
  RECURSIVE_PATTERN = 'recursive_pattern',
  MIRROR_RELATIONSHIP = 'mirror_relationship',
  
  // User-Defined
  CUSTOM = 'custom'
}
```

### ArbitraryConnection Model

```typescript
interface ArbitraryConnection {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  connectionType: ConnectionType;
  
  // Connection Metadata
  strength: number; // 0.0 - 1.0, indicates connection strength
  confidence: number; // 0.0 - 1.0, confidence in connection accuracy
  bidirectional: boolean; // whether connection works both ways
  
  // Descriptive Information
  title?: string;
  description?: string;
  reason?: string; // why this connection exists
  evidence?: string[]; // supporting evidence for connection
  
  // Visual Presentation
  visualStyle?: {
    color?: string;
    thickness?: number;
    dashPattern?: number[];
    opacity?: number;
    label?: string;
    iconType?: string;
  };
  
  // Source and Creation
  createdBy: 'system' | 'user' | 'ai';
  creationMethod?: 'manual' | 'semantic_analysis' | 'visual_analysis' | 'pattern_detection';
  
  // Temporal Information
  createdAt: DateTime;
  updatedAt: DateTime;
  
  // Validation and Quality
  verified: boolean;
  userRating?: number; // 1-5 user rating of connection quality
  
  // Context
  tags?: string[];
  metadata?: {
    [key: string]: any;
  };
}
```

### Extended Node Model

```typescript
interface GraphNode extends AudioRecording {
  // Incoming arbitrary connections
  incomingConnections: ArbitraryConnection[];
  
  // Outgoing arbitrary connections  
  outgoingConnections: ArbitraryConnection[];
  
  // Connection statistics
  connectionStats: {
    totalConnections: number;
    connectionsByType: { [key in ConnectionType]: number };
    averageStrength: number;
    highestRatedConnections: ArbitraryConnection[];
  };
  
  // Graph positioning (separate from tree position)
  graphPosition?: {
    x: number;
    y: number;
    cluster?: string; // which visual cluster this belongs to
  };
  
  // Node importance in graph context
  centrality?: {
    degree: number; // number of connections
    betweenness: number; // how often node lies on paths between other nodes
    closeness: number; // average distance to all other nodes
    eigenvector: number; // influence based on connections to important nodes
  };
}
```

## Connection Detection Algorithms

### Automated Connection Discovery

#### 1. Semantic Analysis
```typescript
interface SemanticAnalyzer {
  analyzeTextSimilarity(text1: string, text2: string): Promise<{
    similarity: number;
    commonTopics: string[];
    connectionType: ConnectionType;
    confidence: number;
  }>;
  
  extractEntities(text: string): Promise<{
    characters: string[];
    locations: string[];
    objects: string[];
    concepts: string[];
  }>;
  
  findThematicConnections(nodes: GraphNode[]): Promise<ArbitraryConnection[]>;
}
```

#### 2. Visual Analysis
```typescript
interface VisualAnalyzer {
  analyzeImageSimilarity(image1: string, image2: string): Promise<{
    colorSimilarity: number;
    compositionSimilarity: number;
    styleSimilarity: number;
    overallSimilarity: number;
    dominantColors: string[];
    visualFeatures: string[];
  }>;
  
  detectVisualPatterns(images: string[]): Promise<{
    styleGroups: string[][]; // groups of similar images
    colorPalettes: { [groupId: string]: string[] };
    compositions: { [groupId: string]: string };
  }>;
  
  findVisualConnections(nodes: GraphNode[]): Promise<ArbitraryConnection[]>;
}
```

#### 3. Temporal Pattern Detection
```typescript
interface TemporalAnalyzer {
  detectNarrativePatterns(nodes: GraphNode[]): Promise<{
    storyArcs: {
      nodes: string[];
      arcType: 'rising_action' | 'climax' | 'resolution' | 'parallel_story';
      confidence: number;
    }[];
    
    temporalReferences: {
      sourceNode: string;
      targetNode: string;
      referenceType: 'flashback' | 'foreshadowing' | 'callback';
      textEvidence: string;
    }[];
  }>;
  
  findCausalRelationships(nodes: GraphNode[]): Promise<ArbitraryConnection[]>;
}
```

### Connection Quality Scoring

```typescript
interface ConnectionScorer {
  scoreConnection(connection: ArbitraryConnection): Promise<{
    relevanceScore: number; // how relevant is this connection
    noveltyScore: number; // how surprising/interesting
    coherenceScore: number; // how well it fits with existing connections
    overallQuality: number; // combined score
    
    qualityFactors: {
      textualEvidence: number;
      visualEvidence: number;
      userValidation: number;
      algorithmicConfidence: number;
    };
  }>;
}
```

## User Interface Extensions

### Graph Visualization Modes

#### 1. Force-Directed Graph Layout
```typescript
interface ForceDirectedLayout {
  // Physics simulation parameters
  nodeRepulsion: number; // how much nodes repel each other
  edgeAttraction: number; // how much connected nodes attract
  centralGravity: number; // pull toward center
  
  // Visual clustering
  clusterByConnectionType: boolean;
  clusterByTemporalProximity: boolean;
  clusterBySemanticSimilarity: boolean;
  
  // Connection filtering
  minConnectionStrength: number; // only show strong connections
  visibleConnectionTypes: ConnectionType[];
  maxConnectionsPerNode: number;
}
```

#### 2. Layered Graph View
```typescript
interface LayeredGraphView {
  layers: {
    name: string;
    connectionTypes: ConnectionType[];
    visible: boolean;
    opacity: number;
    color: string;
  }[];
  
  // Layer interactions
  allowLayerBlending: boolean;
  highlightCrossLayerConnections: boolean;
}
```

#### 3. Hybrid Tree-Graph View
```typescript
interface HybridVisualization {
  // Primary structure (always visible)
  primaryStructure: 'tree' | 'graph';
  
  // Overlay connections on tree
  overlayConnections: {
    enabled: boolean;
    connectionTypes: ConnectionType[];
    visualStyle: 'subtle' | 'prominent' | 'highlight_on_hover';
  };
  
  // Transition between views
  transitionMode: 'smooth_morph' | 'fade_switch' | 'slide_switch';
  transitionDuration: number; // milliseconds
}
```

### Interactive Connection Management

#### Connection Creation Tools
```typescript
interface ConnectionCreationUI {
  // Manual connection creation
  dragAndDropMode: boolean; // drag from one node to another
  
  // Connection suggestion system
  suggestionPanel: {
    enabled: boolean;
    maxSuggestions: number;
    suggestionTypes: ('semantic' | 'visual' | 'temporal')[];
    autoRefresh: boolean;
  };
  
  // Batch connection operations
  batchSelection: {
    enabled: boolean;
    maxNodes: number;
    connectionType: ConnectionType;
    bulkCreateEnabled: boolean;
  };
}
```

#### Connection Editing Interface
```typescript
interface ConnectionEditor {
  // Properties panel
  editableProperties: {
    title: boolean;
    description: boolean;
    strength: boolean;
    tags: boolean;
    visualStyle: boolean;
  };
  
  // Validation tools
  validationFeedback: {
    showConfidenceScore: boolean;
    showQualityWarnings: boolean;
    showSimilarConnections: boolean;
  };
  
  // Bulk operations
  bulkEdit: {
    enabled: boolean;
    supportedOperations: ('delete' | 'update_strength' | 'change_type' | 'add_tags')[];
  };
}
```

## Visualization Algorithms

### Graph Layout Algorithms

#### 1. Community Detection
```typescript
interface CommunityDetection {
  algorithm: 'louvain' | 'leiden' | 'infomap' | 'label_propagation';
  
  detectCommunities(nodes: GraphNode[], connections: ArbitraryConnection[]): Promise<{
    communities: {
      id: string;
      nodes: string[];
      strength: number; // how tightly connected this community is
      theme?: string; // detected theme of this community
    }[];
    
    modularityScore: number; // quality of community detection
  }>;
}
```

#### 2. Path Analysis
```typescript
interface PathAnalyzer {
  findShortestPaths(startNode: string, endNode: string): Promise<{
    paths: {
      nodes: string[];
      connections: string[];
      totalWeight: number;
      pathType: string; // semantic, visual, temporal, etc.
    }[];
  }>;
  
  findNarrativePaths(startNode: string): Promise<{
    storylines: {
      nodes: string[];
      arcType: string;
      coherenceScore: number;
    }[];
  }>;
}
```

#### 3. Centrality Analysis
```typescript
interface CentralityAnalyzer {
  calculateCentralities(nodes: GraphNode[]): Promise<{
    [nodeId: string]: {
      degreeCentrality: number;
      betweennessCentrality: number;
      closenessCentrality: number;
      eigenvectorCentrality: number;
      pageRank: number;
      
      // Story-specific centralities
      narrativeImportance: number;
      thematicCentrality: number;
    };
  }>;
  
  identifyKeyNodes(threshold?: number): Promise<string[]>;
}
```

## API Extensions

### Connection Management API

```typescript
interface ConnectionAPI {
  // CRUD operations
  createConnection(connection: Omit<ArbitraryConnection, 'id' | 'createdAt' | 'updatedAt'>): Promise<ArbitraryConnection>;
  getConnection(id: string): Promise<ArbitraryConnection>;
  updateConnection(id: string, updates: Partial<ArbitraryConnection>): Promise<ArbitraryConnection>;
  deleteConnection(id: string): Promise<void>;
  
  // Bulk operations
  createConnections(connections: Omit<ArbitraryConnection, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<ArbitraryConnection[]>;
  deleteConnections(ids: string[]): Promise<void>;
  
  // Query operations
  getConnectionsForNode(nodeId: string, options?: {
    connectionTypes?: ConnectionType[];
    minStrength?: number;
    direction?: 'incoming' | 'outgoing' | 'both';
  }): Promise<ArbitraryConnection[]>;
  
  searchConnections(query: {
    sourceNodeId?: string;
    targetNodeId?: string;
    connectionTypes?: ConnectionType[];
    minStrength?: number;
    tags?: string[];
    createdBy?: string;
  }): Promise<ArbitraryConnection[]>;
}
```

### Graph Analysis API

```typescript
interface GraphAnalysisAPI {
  // Automated discovery
  suggestConnections(nodeId: string, options?: {
    maxSuggestions?: number;
    analysisTypes?: ('semantic' | 'visual' | 'temporal')[];
    minConfidence?: number;
  }): Promise<{
    suggestions: ArbitraryConnection[];
    analysisMetadata: {
      processingTime: number;
      algorithmsUsed: string[];
      totalCandidatesEvaluated: number;
    };
  }>;
  
  // Batch analysis
  analyzeGraph(options?: {
    includeSemanticAnalysis?: boolean;
    includeVisualAnalysis?: boolean;
    includeTemporalAnalysis?: boolean;
    includeCommunityDetection?: boolean;
  }): Promise<{
    newConnections: ArbitraryConnection[];
    communities: Community[];
    centralities: { [nodeId: string]: CentralityScores };
    insights: {
      type: string;
      description: string;
      confidence: number;
      supportingEvidence: string[];
    }[];
  }>;
  
  // Quality assessment
  validateConnections(connectionIds?: string[]): Promise<{
    [connectionId: string]: {
      isValid: boolean;
      qualityScore: number;
      issues?: string[];
      suggestions?: string[];
    };
  }>;
}
```

### Export/Import Extensions

```typescript
interface GraphExportAPI {
  // Standard graph formats
  exportAsGraphML(): Promise<string>;
  exportAsGEXF(): Promise<string>;
  exportAsD3JSON(): Promise<object>;
  exportAsCytoscape(): Promise<object>;
  
  // Custom formats
  exportAsStoryMap(): Promise<{
    nodes: GraphNode[];
    connections: ArbitraryConnection[];
    communities: Community[];
    narrativeStructure: {
      mainArcs: string[][];
      subplots: string[][];
      themes: { [theme: string]: string[] };
    };
  }>;
  
  // Import formats
  importFromGraphML(data: string): Promise<{
    nodesCreated: number;
    connectionsCreated: number;
    errors: string[];
  }>;
  
  importConnections(connections: ArbitraryConnection[]): Promise<{
    created: number;
    updated: number;
    errors: string[];
  }>;
}
```

## Configuration and Settings

### Graph Behavior Configuration

```typescript
interface GraphConfiguration {
  // Automatic connection discovery
  autoDiscovery: {
    enabled: boolean;
    runOnNewContent: boolean;
    runOnSchedule: boolean;
    scheduleInterval: number; // minutes
    
    algorithms: {
      semanticAnalysis: {
        enabled: boolean;
        minSimilarityThreshold: number;
        maxConnectionsPerNode: number;
      };
      
      visualAnalysis: {
        enabled: boolean;
        minSimilarityThreshold: number;
        analyzeColorSimilarity: boolean;
        analyzeComposition: boolean;
        analyzeStyle: boolean;
      };
      
      temporalAnalysis: {
        enabled: boolean;
        detectFlashbacks: boolean;
        detectForeshadowing: boolean;
        detectCausalRelationships: boolean;
      };
    };
  };
  
  // Connection validation
  validation: {
    requireMinimumStrength: boolean;
    minimumStrength: number;
    requireUserApproval: boolean;
    autoDeleteLowQuality: boolean;
    qualityThreshold: number;
  };
  
  // Performance settings
  performance: {
    maxConnectionsToDisplay: number;
    enableConnectionCaching: boolean;
    cacheTTL: number; // seconds
    enableProgressiveLoading: boolean;
    connectionBatchSize: number;
  };
}
```

### Visual Customization

```typescript
interface GraphVisualizationSettings {
  // Node appearance
  nodes: {
    defaultSize: number;
    sizeBasedOnCentrality: boolean;
    colorByConnectionType: boolean;
    showLabels: boolean;
    labelTruncation: number;
  };
  
  // Connection appearance
  connections: {
    defaultThickness: number;
    thicknessBasedOnStrength: boolean;
    colorByType: boolean;
    showLabels: boolean;
    curveConnections: boolean;
    animateConnections: boolean;
  };
  
  // Layout preferences
  layout: {
    defaultAlgorithm: 'force_directed' | 'circular' | 'hierarchical' | 'grid';
    enablePhysicsSimulation: boolean;
    stabilizationTime: number;
    enableClustering: boolean;
    clusterByConnectionType: boolean;
  };
  
  // Interactive features
  interaction: {
    enableHoverEffects: boolean;
    enableClickToExpand: boolean;
    enableDragAndDrop: boolean;
    enableMultiSelect: boolean;
    highlightConnectedNodes: boolean;
    dimUnconnectedNodes: boolean;
  };
}
```

## Integration with Existing System

### Tree-Graph Synchronization

```typescript
interface TreeGraphSync {
  // Maintain consistency between tree and graph views
  syncNodePositions: boolean;
  syncNodeSelection: boolean;
  syncNodeFiltering: boolean;
  
  // Handle conflicts
  onPositionConflict: 'prefer_tree' | 'prefer_graph' | 'user_choice';
  onStructureChange: 'update_graph' | 'preserve_graph' | 'ask_user';
}
```

### Database Schema Extensions

```sql
-- Arbitrary connections table
CREATE TABLE arbitrary_connections (
  id VARCHAR PRIMARY KEY,
  source_node_id VARCHAR NOT NULL,
  target_node_id VARCHAR NOT NULL,
  connection_type VARCHAR NOT NULL,
  
  strength REAL DEFAULT 0.5,
  confidence REAL DEFAULT 0.5,
  bidirectional BOOLEAN DEFAULT FALSE,
  
  title VARCHAR,
  description TEXT,
  reason TEXT,
  evidence JSON,
  
  visual_style JSON,
  
  created_by VARCHAR NOT NULL,
  creation_method VARCHAR,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  verified BOOLEAN DEFAULT FALSE,
  user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
  
  tags JSON,
  metadata JSON,
  
  FOREIGN KEY (source_node_id) REFERENCES audio_recordings(id) ON DELETE CASCADE,
  FOREIGN KEY (target_node_id) REFERENCES audio_recordings(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_connections_source ON arbitrary_connections(source_node_id);
CREATE INDEX idx_connections_target ON arbitrary_connections(target_node_id);
CREATE INDEX idx_connections_type ON arbitrary_connections(connection_type);
CREATE INDEX idx_connections_strength ON arbitrary_connections(strength);
CREATE INDEX idx_connections_created_at ON arbitrary_connections(created_at);

-- Connection analytics table
CREATE TABLE connection_analytics (
  id VARCHAR PRIMARY KEY,
  connection_id VARCHAR NOT NULL,
  metric_name VARCHAR NOT NULL,
  metric_value REAL NOT NULL,
  calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (connection_id) REFERENCES arbitrary_connections(id) ON DELETE CASCADE
);
```

## Future Extensions

### AI-Powered Enhancements

1. **Large Language Model Integration**
   - Use LLMs to understand connection semantics
   - Generate natural language explanations for connections
   - Detect narrative patterns and story structures

2. **Computer Vision Integration**
   - Advanced image similarity detection
   - Style transfer analysis
   - Visual motif detection

3. **Graph Neural Networks**
   - Learn connection patterns from user behavior
   - Predict likely connections
   - Optimize graph layout based on usage patterns

### Advanced Visualization Features

1. **3D Graph Visualization**
   - Three-dimensional node positioning
   - Temporal layers in z-axis
   - VR/AR support for immersive exploration

2. **Dynamic Graph Evolution**
   - Time-based graph animations
   - Connection strength evolution over time
   - Narrative flow visualization

3. **Multi-Modal Integration**
   - Audio waveform overlays on connections
   - Video timeline integration
   - Interactive media playback in graph context

## Implementation Roadmap

### Phase 1: Core Infrastructure
- [ ] Basic ArbitraryConnection data model
- [ ] Connection CRUD API
- [ ] Simple graph visualization
- [ ] Manual connection creation UI

### Phase 2: Automated Discovery
- [ ] Semantic analysis integration
- [ ] Visual analysis for images
- [ ] Basic connection suggestions
- [ ] Quality scoring system

### Phase 3: Advanced Visualization
- [ ] Force-directed graph layout
- [ ] Multi-layer visualization
- [ ] Interactive graph editing
- [ ] Export/import capabilities

### Phase 4: Intelligence Features
- [ ] Community detection
- [ ] Centrality analysis
- [ ] Narrative path finding
- [ ] Advanced AI integration

### Phase 5: User Experience
- [ ] Hybrid tree-graph views
- [ ] Advanced filtering and search
- [ ] Collaboration features
- [ ] Performance optimizations

## Conclusion

This specification extends the branches-conversation-tree system to support rich, arbitrary graph connections while maintaining the core hierarchical structure. The design enables:

- **Flexible Relationships**: Beyond parent-child to thematic, causal, and visual connections
- **Intelligent Discovery**: AI-powered connection suggestion and validation
- **Rich Visualization**: Multiple graph layout algorithms and interactive features  
- **User Control**: Manual override and customization of all automated features
- **Performance**: Scalable design for large graphs with thousands of connections
- **Integration**: Seamless coexistence with existing tree-based functionality

The result is a powerful extension that transforms the system from a simple conversation tree into a rich, interconnected knowledge graph that can reveal hidden patterns and relationships in creative storytelling.

---

*This specification is designed to be implemented incrementally, with each phase building on the previous while maintaining backward compatibility with the existing system.*
