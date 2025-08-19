import { AppController } from './core/AppController.js';

document.addEventListener('DOMContentLoaded', () => {
  const app = new AppController({
    selectors: {
      treeContainer: '#tree-visualization',
      resetZoom: '#resetZoom',
      expandAll: '#expandAll',
      collapseAll: '#collapseAll',
      layoutToggle: '#layoutToggle',
      rootSelector: '#rootSelector',
      nodeDetails: '#node-details',
      imagesContainer: '#images-container',
      audio: {
        player: '#audio-player',
        placeholder: '#audio-placeholder'
      }
    }
  });
  window.appV2 = app;
});
