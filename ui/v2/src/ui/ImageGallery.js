import { MediaService } from '../services/MediaService.js';

export class ImageGallery {
  constructor(selector, api){ this.root = document.querySelector(selector); this.api = api; this.media = new MediaService(); }
  render(images){
    if(!images || images.length===0){ this.root.innerHTML = '<p class="muted">No images available for this recording.</p>'; return; }
    this.root.innerHTML = images.map(img => `
      <div class="image-item">
        <img src="${this.media.imageUrl(img.image_file_path)}" alt="Generated image" onerror="this.style.display='none'" />
        <div class="image-prompt">${img.prompt||''}</div>
        <div class="image-meta"><span>Seed: ${img.seed||'N/A'}</span><span>${new Date(img.created_date).toLocaleDateString()}</span></div>
      </div>
    `).join('');
  }
}
