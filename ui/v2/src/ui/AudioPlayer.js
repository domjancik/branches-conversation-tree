import { MediaService } from '../services/MediaService.js';

export class AudioPlayer {
  constructor(sel){
    this.player = document.querySelector(sel.player);
    this.placeholder = document.querySelector(sel.placeholder);
    this.media = new MediaService();
  }
  async load(node){
    if(node.fullPath){
      const url = this.media.audioUrl(node.fullPath);
      const sources = this.player.getElementsByTagName('source');
      for(const s of sources) s.src = url;
      this.player.style.display = 'block';
      this.placeholder.style.display = 'none';
      this.player.onerror = () => { this.player.style.display='none'; this.placeholder.style.display='block'; this.placeholder.textContent='Audio not available'; };
      this.player.load();
    } else {
      this.player.style.display = 'none';
      this.placeholder.style.display = 'block';
      this.placeholder.textContent = 'No audio file available';
    }
  }
}
