export class MediaService {
  audioUrl(fullPath){ return `/audio/${encodeURIComponent(fullPath)}`; }
  imageUrl(path){ return `/images/${encodeURIComponent(path)}`; }
}
