# Branches Conversation Tree - Multi-Directional Implementation Specification

## Overview

This specification defines a unified framework for implementing the branches-conversation-tree system from multiple directions while maintaining interoperability through common data structures, contracts, and message buses. The goal is to enable different implementations (UI-first, API-first, database-first, etc.) to work together seamlessly.

## Core Concepts

### System Purpose
The branches-conversation-tree is a creative AI storytelling platform that:
- Processes audio conversations into visual stories
- Uses LLM-generated prompts for image generation
- Maintains hierarchical tree structures of conversations
- Supports multi-modal content generation (audio → text → images → videos)

### Multi-Directional Approach
Different development teams or individuals can implement the system from various entry points:
- **UI-First**: Start with visual interfaces and work backward to data
- **API-First**: Begin with service contracts and build outward
- **Data-First**: Design database schema and build upward
- **Pipeline-First**: Focus on processing workflows and connect to storage/UI
- **Integration-First**: Connect existing services and build missing pieces

## Common Data Structures

### Core Data Models

#### AudioRecording
```typescript
interface AudioRecording {
  id: string;
  audioFilePath: string;
  transcription?: string;
  prompts?: string[];
  parentAudioRecordingId?: string;
  parentTime?: number;
  duration?: number;
  createdAt: DateTime;
  updatedAt: DateTime;
  children?: AudioRecording[];
  imageGenerations?: RecordingImageGeneration[];
}
```

#### RecordingImageGeneration
```typescript
interface RecordingImageGeneration {
  id: string;
  audioRecordingId: string;
  imageFilePath?: string;
  seed?: number;
  prompt: string;
  reason?: string;
  duration?: number;
  requestPayload?: object;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  createdAt: DateTime;
  updatedAt: DateTime;
}
```

#### ProcessingTask
```typescript
interface ProcessingTask {
  id: string;
  type: 'transcription' | 'prompt_generation' | 'image_generation' | 'video_generation';
  status: 'queued' | 'processing' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  input: object;
  output?: object;
  error?: string;
  progress: number; // 0-1
  createdAt: DateTime;
  updatedAt: DateTime;
  relatedRecordingId?: string;
}
```

#### TreeNode (Generic)
```typescript
interface TreeNode<T> {
  id: string;
  data: T;
  parentId?: string;
  children: TreeNode<T>[];
  depth: number;
  position: {
    x: number;
    y: number;
  };
  metadata: {
    [key: string]: any;
  };
}
```

### Event System

#### Event Types
```typescript
type SystemEvent = 
  | AudioRecordingCreated
  | TranscriptionCompleted
  | PromptsGenerated
  | ImageGenerationStarted
  | ImageGenerationCompleted
  | VideoGenerationStarted
  | VideoGenerationCompleted
  | ProcessingError;

interface BaseEvent {
  id: string;
  type: string;
  timestamp: DateTime;
  source: string;
  recordingId?: string;
}

interface AudioRecordingCreated extends BaseEvent {
  type: 'audio_recording_created';
  data: {
    recording: AudioRecording;
    audioFilePath: string;
  };
}

interface TranscriptionCompleted extends BaseEvent {
  type: 'transcription_completed';
  data: {
    recordingId: string;
    transcription: string;
    duration: number;
  };
}

interface PromptsGenerated extends BaseEvent {
  type: 'prompts_generated';
  data: {
    recordingId: string;
    prompts: string[];
    model: string;
  };
}

interface ImageGenerationCompleted extends BaseEvent {
  type: 'image_generation_completed';
  data: {
    imageGenerationId: string;
    imageFilePath: string;
    seed: number;
    duration: number;
  };
}
```

## Service Contracts

### Core API Interfaces

#### Data Storage Service
```typescript
interface DataStorageService {
  // Audio Recordings
  createRecording(request: CreateRecordingRequest): Promise<AudioRecording>;
  getRecording(id: string): Promise<AudioRecording>;
  updateRecording(id: string, updates: Partial<AudioRecording>): Promise<AudioRecording>;
  deleteRecording(id: string): Promise<void>;
  getRecordingTree(rootId?: string): Promise<TreeNode<AudioRecording>>;
  
  // Image Generations
  createImageGeneration(request: CreateImageGenerationRequest): Promise<RecordingImageGeneration>;
  updateImageGeneration(id: string, updates: Partial<RecordingImageGeneration>): Promise<RecordingImageGeneration>;
  getImageGenerations(recordingId: string): Promise<RecordingImageGeneration[]>;
  
  // Context and Relationships
  getParentContext(recordingId: string, depth?: number): Promise<AudioRecording[]>;
  getChildrenContext(recordingId: string, depth?: number): Promise<AudioRecording[]>;
}
```

#### Processing Service
```typescript
interface ProcessingService {
  // Audio Processing
  transcribeAudio(audioFilePath: string): Promise<string>;
  generatePrompts(text: string, model?: string, count?: number): Promise<string[]>;
  
  // Image Generation
  generateImage(prompt: string, style?: string[], negativePrompt?: string): Promise<ImageGenerationResult>;
  
  // Video Generation
  generateVideo(imagePath: string, movementPrompt?: string): Promise<VideoGenerationResult>;
  
  // Queue Management
  queueTask(task: ProcessingTask): Promise<string>;
  getTaskStatus(taskId: string): Promise<ProcessingTask>;
  cancelTask(taskId: string): Promise<void>;
}
```

#### Event Bus Service
```typescript
interface EventBusService {
  publish(event: SystemEvent): Promise<void>;
  subscribe(eventType: string, handler: (event: SystemEvent) => Promise<void>): Promise<string>;
  unsubscribe(subscriptionId: string): Promise<void>;
  
  // Message Queue Integration
  sendCommand(command: Command): Promise<void>;
  waitForCommand(agentId: string, filters?: CommandFilters): Promise<Command>;
}
```

#### Visualization Service
```typescript
interface VisualizationService {
  // Tree Visualization
  getTreeLayout(nodes: TreeNode<any>[]): Promise<TreeLayout>;
  updateNodePosition(nodeId: string, position: {x: number, y: number}): Promise<void>;
  
  // UI State Management
  getUIState(viewId: string): Promise<UIState>;
  updateUIState(viewId: string, state: Partial<UIState>): Promise<void>;
  
  // Export/Import
  exportTree(format: 'json' | 'svg' | 'png'): Promise<Blob>;
  importTree(data: Blob | string): Promise<TreeNode<AudioRecording>>;
}
```

## Message Bus Architecture

### Command Pattern
```typescript
interface Command {
  id: string;
  type: string;
  payload: object;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  targetComponentIds?: string[];
  source: string;
  timestamp: DateTime;
}

interface CommandResponse {
  commandId: string;
  status: 'success' | 'error' | 'in_progress';
  result?: object;
  error?: string;
  timestamp: DateTime;
}
```

### Queue System
```typescript
interface QueueManager {
  enqueue(queue: string, item: any, priority?: number): Promise<void>;
  dequeue(queue: string): Promise<any>;
  peek(queue: string): Promise<any>;
  size(queue: string): Promise<number>;
  clear(queue: string): Promise<void>;
}

// Standard Queue Names
const QUEUE_NAMES = {
  TRANSCRIPTION: 'transcription_queue',
  PROMPT_GENERATION: 'prompt_generation_queue',
  IMAGE_GENERATION: 'image_generation_queue',
  VIDEO_GENERATION: 'video_generation_queue',
  UI_UPDATES: 'ui_updates_queue',
  EVENTS: 'events_queue'
} as const;
```

### Pub/Sub Pattern
```typescript
interface PubSubService {
  publish(channel: string, message: any): Promise<void>;
  subscribe(channel: string, callback: (message: any) => Promise<void>): Promise<string>;
  unsubscribe(subscriptionId: string): Promise<void>;
  
  // Channel Naming Convention
  // Format: {domain}.{entity}.{action}
  // Examples:
  // - audio.recording.created
  // - processing.transcription.completed
  // - ui.node.selected
  // - system.error.occurred
}
```

## Implementation Strategies

### 1. UI-First Implementation
**Entry Point**: Start with visual components and work backward

**Approach**:
1. Design tree visualization components
2. Create mock data services
3. Implement real-time UI updates
4. Connect to actual data sources
5. Add processing capabilities

**Key Components**:
- Tree visualization engine
- Node interaction handlers
- Real-time update mechanisms
- State management
- Mock data generators

### 2. API-First Implementation
**Entry Point**: Define service contracts and implement APIs

**Approach**:
1. Design API contracts and schemas
2. Implement data storage APIs
3. Add processing service APIs
4. Create event publishing mechanisms
5. Build client interfaces

**Key Components**:
- REST/GraphQL API servers
- Database adapters
- Service orchestration
- API documentation
- Client SDKs

### 3. Data-First Implementation
**Entry Point**: Design database schema and data models

**Approach**:
1. Design normalized database schema
2. Implement data access layers
3. Add business logic services
4. Create API endpoints
5. Build user interfaces

**Key Components**:
- Database migrations
- ORM/Data mapper
- Repository patterns
- Transaction management
- Data validation

### 4. Pipeline-First Implementation
**Entry Point**: Focus on processing workflows

**Approach**:
1. Design processing pipelines
2. Implement worker services
3. Add queue management
4. Connect to storage systems
5. Build monitoring interfaces

**Key Components**:
- Workflow orchestration
- Worker processes
- Queue systems
- Monitoring dashboards
- Error handling

### 5. Integration-First Implementation
**Entry Point**: Connect existing services and fill gaps

**Approach**:
1. Map existing service capabilities
2. Design integration contracts
3. Implement service adapters
4. Add missing functionality
5. Create unified interfaces

**Key Components**:
- Service adapters
- Protocol translators
- Configuration management
- Health monitoring
- Fallback mechanisms

## Common Protocols and Standards

### HTTP API Standards
```typescript
// RESTful endpoint naming
interface APIEndpoints {
  // Audio Recordings
  'GET /api/v1/recordings': GetRecordingsResponse;
  'POST /api/v1/recordings': CreateRecordingRequest;
  'GET /api/v1/recordings/:id': AudioRecording;
  'PUT /api/v1/recordings/:id': UpdateRecordingRequest;
  'DELETE /api/v1/recordings/:id': void;
  'GET /api/v1/recordings/:id/tree': TreeNode<AudioRecording>;
  
  // Image Generations
  'GET /api/v1/recordings/:id/images': RecordingImageGeneration[];
  'POST /api/v1/recordings/:id/images': CreateImageGenerationRequest;
  'PUT /api/v1/images/:id': UpdateImageGenerationRequest;
  
  // Processing
  'POST /api/v1/process/audio': ProcessAudioRequest;
  'GET /api/v1/process/tasks/:id': ProcessingTask;
  'POST /api/v1/process/tasks/:id/cancel': void;
  
  // Events
  'GET /api/v1/events/stream': EventStream; // Server-Sent Events
  'POST /api/v1/events': PublishEventRequest;
}
```

### WebSocket Protocol
```typescript
interface WebSocketMessage {
  type: 'command' | 'event' | 'response' | 'heartbeat';
  id: string;
  timestamp: DateTime;
  payload: any;
}

// Message Types
type WSMessageType = 
  | 'node.selected'
  | 'node.updated'
  | 'tree.refreshed'
  | 'processing.started'
  | 'processing.completed'
  | 'ui.state.changed';
```

### File Storage Conventions
```typescript
interface FileStorageStructure {
  audio: {
    recordings: '/recordings/{recordingId}/{timestamp}.{ext}';
    transcriptions: '/recordings/{recordingId}/transcription.txt';
  };
  images: {
    generated: '/images/{recordingId}/{imageGenerationId}.{ext}';
    thumbnails: '/images/{recordingId}/thumbs/{imageGenerationId}.{ext}';
  };
  videos: {
    generated: '/videos/{recordingId}/{videoGenerationId}.{ext}';
    thumbnails: '/videos/{recordingId}/thumbs/{videoGenerationId}.{ext}';
  };
  metadata: {
    recordings: '/metadata/recordings/{recordingId}.json';
    processing: '/metadata/processing/{taskId}.json';
  };
}
```

## Configuration Management

### Environment Configuration
```typescript
interface SystemConfig {
  // Database
  database: {
    type: 'sqlite' | 'postgresql' | 'mysql';
    connectionString: string;
    poolSize?: number;
    timeout?: number;
  };
  
  // External Services
  services: {
    ollama: {
      baseUrl: string;
      timeout?: number;
      defaultModel?: string;
    };
    fooocus: {
      baseUrl: string;
      timeout?: number;
      defaultStyles?: string[];
    };
    framepack: {
      baseUrl: string;
      timeout?: number;
    };
  };
  
  // Processing
  processing: {
    maxConcurrentTasks: number;
    queueSize: number;
    retryAttempts: number;
    whisperModel: string;
  };
  
  // Storage
  storage: {
    basePath: string;
    maxFileSize: number;
    allowedExtensions: string[];
  };
  
  // UI
  ui: {
    theme: 'light' | 'dark';
    autoRefresh: boolean;
    maxTreeDepth: number;
  };
}
```

### Feature Flags
```typescript
interface FeatureFlags {
  streamDiffusionBackend: boolean;
  videoGeneration: boolean;
  realTimeProcessing: boolean;
  advancedVisualization: boolean;
  audioInterface: boolean;
  multiLanguageSupport: boolean;
}
```

## Testing Strategies

### Contract Testing
```typescript
interface ContractTest {
  service: string;
  operation: string;
  input: any;
  expectedOutput: any;
  constraints?: {
    responseTime?: number;
    errorConditions?: string[];
  };
}
```

### Integration Testing
```typescript
interface IntegrationTestSuite {
  // End-to-End Workflows
  'audio-to-image-pipeline': {
    input: { audioFile: string };
    expectedSteps: string[];
    timeout: number;
  };
  
  'tree-visualization-update': {
    input: { treeData: TreeNode<AudioRecording> };
    expectedOutputs: string[];
  };
  
  // Service Integration
  'data-api-integration': {
    endpoints: string[];
    scenarios: IntegrationScenario[];
  };
}
```

## Monitoring and Observability

### Metrics Collection
```typescript
interface SystemMetrics {
  processing: {
    transcriptionLatency: number;
    imageGenerationLatency: number;
    queueSize: number;
    errorRate: number;
  };
  
  storage: {
    databaseConnections: number;
    storageUsage: number;
    queryLatency: number;
  };
  
  ui: {
    activeUsers: number;
    renderTime: number;
    interactionRate: number;
  };
}
```

### Health Checks
```typescript
interface HealthCheck {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency: number;
  lastCheck: DateTime;
  details?: {
    [key: string]: any;
  };
}
```

## Migration and Compatibility

### Version Management
```typescript
interface VersionInfo {
  api: string;          // e.g., "v1.0.0"
  database: string;     // e.g., "20250819_001"
  ui: string;           // e.g., "2.1.0"
  protocols: {
    websocket: string;  // e.g., "1.0"
    eventBus: string;   // e.g., "1.1"
  };
}
```

### Migration Strategy
```typescript
interface MigrationPlan {
  from: VersionInfo;
  to: VersionInfo;
  steps: MigrationStep[];
  rollbackPlan: MigrationStep[];
  validation: ValidationRule[];
}
```

## Security Considerations

### Authentication & Authorization
```typescript
interface SecurityConfig {
  authentication: {
    type: 'none' | 'basic' | 'jwt' | 'oauth2';
    config: any;
  };
  
  authorization: {
    roles: string[];
    permissions: {
      [role: string]: string[];
    };
  };
  
  api: {
    rateLimiting: {
      enabled: boolean;
      requests: number;
      window: number; // seconds
    };
    cors: {
      origins: string[];
      methods: string[];
    };
  };
}
```

## Deployment Patterns

### Container Configuration
```dockerfile
# Example service container
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
```

### Service Discovery
```typescript
interface ServiceRegistry {
  register(service: ServiceInfo): Promise<void>;
  discover(serviceName: string): Promise<ServiceInfo[]>;
  healthCheck(serviceId: string): Promise<HealthStatus>;
  deregister(serviceId: string): Promise<void>;
}
```

## Implementation Guidelines

### 1. Start Small, Think Big
- Begin with core data structures
- Implement minimal viable contracts
- Add complexity incrementally
- Maintain backward compatibility

### 2. Contract-First Development
- Define interfaces before implementation
- Use schema validation
- Document expected behaviors
- Test contract compliance

### 3. Event-Driven Architecture
- Emit events for all significant changes
- Keep event payloads immutable
- Use consistent event naming
- Support event replay for debugging

### 4. Fail Gracefully
- Implement circuit breakers
- Provide meaningful error messages
- Support graceful degradation
- Log errors with context

### 5. Monitor Everything
- Track performance metrics
- Monitor health endpoints
- Log user interactions
- Alert on anomalies

## Conclusion

This specification provides a comprehensive framework for implementing the branches-conversation-tree system from any direction while maintaining interoperability. The key principles are:

1. **Common Data Contracts**: Ensure all implementations use the same data structures
2. **Service Boundaries**: Well-defined interfaces between components
3. **Event-Driven Communication**: Loose coupling through events and messages
4. **Configuration Management**: Flexible configuration for different environments
5. **Testing Strategy**: Comprehensive testing at all levels
6. **Monitoring**: Observability built into the system from the start

By following this specification, different teams or individuals can work on different aspects of the system while ensuring their implementations will work together seamlessly.

---

*This specification is a living document that should be updated as the system evolves and new requirements emerge.*
