import { EventBus } from './EventBus.js';
import { StateManager } from './StateManager.js';
import { ApiService } from '../services/ApiService.js';
import { ConfigService } from '../services/ConfigService.js';
import { MediaService } from '../services/MediaService.js';
import { TreeRenderer } from '../visualization/TreeRenderer.js';
import { LayoutManager } from '../visualization/LayoutManager.js';
import { DetailsPanel } from '../ui/DetailsPanel.js';
import { AudioPlayer } from '../ui/AudioPlayer.js';
import { ImageGallery } from '../ui/ImageGallery.js';
import { ControlsPanel } from '../ui/ControlsPanel.js';

export class AppController {
  constructor(opts){
    this.bus = new EventBus();
    this.state = new StateManager(this.bus);
    this.api = new ApiService();
    this.config = new ConfigService();
    this.media = new MediaService();

    this.layout = new LayoutManager(this.state, this.bus);
    this.tree = new TreeRenderer({ container: opts.selectors.treeContainer, state: this.state, bus: this.bus });
    this.details = new DetailsPanel(opts.selectors.nodeDetails);
    this.audio = new AudioPlayer(opts.selectors.audio);
    this.images = new ImageGallery(opts.selectors.imagesContainer, this.api);
    this.controls = new ControlsPanel({ selectors: opts.selectors, state: this.state, bus: this.bus });

    this.init();
  }

  async init(){
    await this.loadConfig();
    await this.loadData();
    this.tree.init();
    this.controls.init();

    // subscriptions
    this.bus.on('node:selected', async (node) => {
      this.state.set('selectedNode', node);
      this.details.render(node.data);
      await this.audio.load(node.data);
      const imgs = await this.api.loadImages(node.data.id);
      this.images.render(imgs);
    });

    this.bus.on('layout:toggle', () => {
      this.layout.toggle();
      this.tree.render();
    });

    this.bus.on('tree:resetZoom', () => this.tree.resetZoom());
    this.bus.on('tree:expandAll', () => { this.tree.expandAll(); this.tree.render(); });
    this.bus.on('tree:collapseAll', () => { this.tree.collapseAll(); this.tree.render(); });

    // initial render
    this.tree.render();
  }

  async loadConfig(){
    const cfg = await this.api.loadConfig();
    this.config.set(cfg);
    this.state.set('config', cfg);
  }

  async loadData(){
    const data = await this.api.loadTreeData();
    this.state.set('data', data);
    this.controls.populateRoots(data.roots||[]);
    this.tree.setRootIndex(0);
  }
}
