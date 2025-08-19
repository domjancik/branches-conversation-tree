export class NodeFactory {
  constructor(state){ this.state = state; }
  enter(selection){
    const cfg = this.state.get('config');
    const radius = cfg.nodeRadius || 8;
    const blockWidth = cfg.nodeBlockWidth || 240; // wider to accommodate text
    const blockMaxHeight = cfg.nodeBlockMaxHeight || 140;

    // Base node dot
    selection.append('circle')
      .attr('r', radius)
      .style('cursor','pointer');

    // Wrapped text block under the node using foreignObject
    // Center horizontally beneath the circle
    const fo = selection.append('foreignObject')
      .attr('class','node-fo')
      .attr('x', -blockWidth/2)
      .attr('y', radius + 8)
      .attr('width', blockWidth)
      .attr('height', blockMaxHeight)
      .style('overflow','visible');

    fo.append('xhtml:div')
      .attr('class','node-label')
      .html(d => {
        const name = d.data.name || '';
        const desc = (d.data.transcriptionPreview || d.data.transcription || '').trim();
        return `
          <div class="title">${name}</div>
          ${desc ? `<div class="desc">${desc}</div>` : ''}
        `;
      });
  }
}
