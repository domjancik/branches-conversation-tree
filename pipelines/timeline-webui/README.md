# Timeline WebUI — Media Existence Visualization

This pipeline provides a local web UI that visualizes media files (images, audio, video) in a directory as horizontal bars across time. Images are fixed-width bars; audio/video are duration-based bars. Start times prefer media metadata (e.g., EXIF DateTimeOriginal) with filesystem modified time as a fallback.

Features
- Pick a directory (File System Access API)
- Optional recursive include with file limit
- Canvas-based timeline with a dedicated top control row for panning/zooming
- Zoom with Ctrl/Cmd + mouse wheel anywhere or mouse wheel on top row
- Adjustable image bar width and max row count

Requirements
- Chromium-based browser (File System Access API)
- Must be served over http(s) (localhost is okay). Opening index.html directly (file://) will likely disable directory access.

Run locally (PowerShell)
- From this folder, run:
  
  1. `./start_ui.ps1`
  2. Open the printed URL in your browser (e.g., http://localhost:8742)

Usage
1. Click “Pick Directory” and select the folder to visualize.
2. Toggle “Recursive” to include subdirectories and set a file “Limit”.
3. Use the top strip to pan (drag) and zoom (mouse wheel); Ctrl/Cmd + wheel also zooms.
4. Adjust “Image width” (px) and “Rows” to tune the display.

Notes
- Image start time uses EXIF when available (via exifr). Otherwise falls back to file modified time.
- Audio/video duration is derived via HTML media metadata (loadedmetadata). Creation time for audio/video currently falls back to file modified time.
- Performance: metadata parsing uses a small worker pool and periodic partial redraws for responsiveness.
- Future enhancements: virtualized rows, more container metadata (e.g., MP4 creation_time), filters, grouping by day.

