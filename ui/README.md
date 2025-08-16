# Branches Conversation Tree UI

A web-based visualization tool for displaying conversation tree data from SQLite database, similar to git branches visualization, with integrated image display.

## Features

- **Interactive Tree Visualization**: Git branches-like tree layout using D3.js
- **Node Details**: Click on nodes to view detailed information including transcription, duration, and metadata
- **Image Integration**: Display generated images associated with each recording
- **Interactive Controls**: Expand/collapse branches, zoom, pan, and reset view
- **Responsive Design**: Works on desktop and mobile devices

## Database Structure

The application reads from an SQLite database with two main tables:
- `audio_recordings`: Contains conversation recordings with parent-child relationships
- `recording_image_generations`: Contains generated images linked to recordings

## Setup and Installation

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Database Configuration**
   - Ensure your SQLite database is located at: `C:\\Users\\magne\\Documents\\Branches-ConversationTree\\Branches-ConversationTree-DB.db`
   - Images should be in the same directory as the database

3. **Start the Server**
   ```bash
   npm start
   ```

4. **Development Mode** (with auto-restart)
   ```bash
   npm run dev
   ```

5. **Access the Application**
   - Open your browser and go to: http://localhost:3000

## Usage

### Navigation
- **Click on nodes** to expand/collapse branches and view details
- **Drag** to pan around the visualization
- **Mouse wheel** or pinch to zoom in/out
- **Reset View** button to return to initial position

### Controls
- **Expand All**: Show all branches at once
- **Collapse All**: Collapse all branches to show only root nodes
- **Reset View**: Reset zoom and position

### Node Information
Click on any node to see:
- Recording ID and filename
- Duration and creation date
- Parent relationship and branch time
- Full transcription text
- Associated generated images with prompts

### Image Display
- Images are displayed in the right panel when a node is selected
- Each image shows the generation prompt and metadata
- Images are loaded from the same directory as the database

## API Endpoints

- `GET /api/tree-data` - Get hierarchical tree structure
- `GET /api/recordings` - Get all recordings
- `GET /api/recordings/:id/images` - Get images for a specific recording
- `GET /api/images` - Get all images with recording relationships
- `GET /images/:filename` - Serve image files

## Technology Stack

- **Backend**: Node.js, Express.js, SQLite3
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Visualization**: D3.js v7
- **Database**: SQLite (read-only access)

## File Structure

```
ui/
├── server.js              # Express server with SQLite integration
├── package.json           # Dependencies and scripts
├── README.md             # This file
└── public/
    ├── index.html        # Main HTML page
    ├── styles.css        # CSS styles
    └── app.js           # JavaScript application logic
```

## Customization

### Styling
Edit `public/styles.css` to customize:
- Color scheme
- Layout dimensions
- Typography
- Node and link appearance

### Visualization Behavior
Edit `public/app.js` to modify:
- Tree layout parameters
- Animation duration
- Node sizing and positioning
- Interaction behavior

### Database Configuration
Edit `server.js` to change:
- Database path
- Query logic
- API endpoints
- Image serving location

## Troubleshooting

### Database Connection Issues
- Ensure the database file exists at the specified path
- Check that the database is not locked by another application
- Verify read permissions on the database file

### Images Not Loading
- Confirm images are in the same directory as the database
- Check that image file paths in the database are correct
- Ensure proper file permissions

### Performance Issues
- For large datasets, consider adding pagination to the tree view
- Implement virtual scrolling for image galleries
- Add database indexing for better query performance

## License

MIT License - feel free to modify and distribute as needed.
