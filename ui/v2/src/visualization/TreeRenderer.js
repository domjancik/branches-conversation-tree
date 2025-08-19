import { TooltipManager } from '../ui/TooltipManager.js';
import { NodeFactory } from './NodeFactory.js';

export class TreeRenderer {
  constructor({ container, state, bus }){
    this.state = state; this.bus = bus; this.containerSel = container;
    this.nodeFactory = new NodeFactory(state);
    this.tooltip = new TooltipManager();
    this.nodeIdCounter = 0;
  }

  init(){
    const margin = this.state.get('config').treeMargin || {top:40,right:40,bottom:40,left:40};
    this.margin = margin;
    const el = document.querySelector(this.containerSel);
    this.width = el.clientWidth - margin.left - margin.right;
    this.height = el.clientHeight - margin.top - margin.bottom;

    this.svg = d3.select(this.containerSel).append('svg').attr('width','100%').attr('height','100%')
      .call(d3.zoom().on('zoom', ev => this.g.attr('transform', ev.transform)))
      .on('dblclick.zoom', null);
    this.g = this.svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    this.setupLayout();

    // events
    this.bus.on('root:change', (idx)=> { this.setRootIndex(idx); this.render(); this.resetZoom(); });
    window.addEventListener('resize', ()=> this.onResize());
  }

  setupLayout(){
    const layout = this.state.get('layout');
    const [a,b] = layout==='horizontal' ? [this.height, this.width] : [this.width, this.height];
    this.tree = d3.tree().size([a,b]);
    const data = this.state.get('data');
    if(data && data.roots && data.roots.length>0){
      const idx = this.state.get('rootIndex')||0;
      this.root = d3.hierarchy(data.roots[idx], d=> d.children);
      if(layout==='horizontal'){ this.root.x0 = this.height/2; this.root.y0 = 0; }
      else { this.root.x0 = this.width/2; this.root.y0 = 0; }
    }
  }

  setRootIndex(i){ this.state.set('rootIndex', i); this.setupLayout(); }

  render(){
    if(!this.root) return;
    const treeData = this.tree(this.root);
    const nodes = treeData.descendants();
    const links = treeData.descendants().slice(1);

    // nodes
    const node = this.g.selectAll('.node').data(nodes, d=> d.id || (d.id = ++this.nodeIdCounter));
    const enter = node.enter().append('g').attr('class','node')
      .attr('transform', _=> `translate(${this.root.x0||0},${this.root.y0||0})`)
      .on('click', (ev,d)=> this.onSelect(d, ev))
      .on('dblclick', (ev,d)=> this.onToggle(d))
      .on('mouseover', (ev,d)=> this.tooltip.show(`<strong>${d.data.name}</strong>`, ev.pageX, ev.pageY))
      .on('mouseout', ()=> this.tooltip.hide());

    this.nodeFactory.enter(enter);

    const upd = enter.merge(node);
    upd.transition().duration(this.state.get('config').animationDuration||750)
      .attr('transform', d=> this.state.get('layout')==='horizontal' ? `translate(${d.y},${d.x})` : `translate(${d.x},${d.y})`);

    node.exit().remove();

    // links
    const link = this.g.selectAll('.link').data(links, d=> d.id);
    const linkEnter = link.enter().insert('path','g').attr('class','link')
      .attr('d', d=> this._diagonal({x:this.root.x0,y:this.root.y0}, {x:this.root.x0,y:this.root.y0}));
    linkEnter.merge(link).transition().duration(this.state.get('config').animationDuration||750)
      .attr('d', d=> this._diagonal(d, d.parent));
    link.exit().remove();

    nodes.forEach(d=>{ d.x0 = d.x; d.y0 = d.y; });
  }

  onSelect(d, ev){ this.bus.emit('node:selected', d); }
  onToggle(d){ if(d.children){ d._children=d.children; d.children=null; } else { d.children=d._children; d._children=null; } this.render(); }

  expandAll(){ const e=(n)=>{ if(n._children){ n.children=n._children; n._children=null; } (n.children||[]).forEach(e);}; e(this.root); }
  collapseAll(){ const c=(n)=>{ if(n.children){ n._children=n.children; n.children=null; } (n._children||[]).forEach(c); }; (this.root.children||[]).forEach(c); }

  resetZoom(){ this.svg.transition().duration(750).call(d3.zoom().transform, d3.zoomIdentity.translate(this.margin.left, this.margin.top)); }
  onResize(){ const el = document.querySelector(this.containerSel); this.width = el.clientWidth - this.margin.left - this.margin.right; this.height = el.clientHeight - this.margin.top - this.margin.bottom; this.setupLayout(); this.render(); }

  _diagonal(s,d){
    if(this.state.get('layout')==='horizontal'){
      return `M ${s.y} ${s.x} C ${s.y+24} ${s.x}, ${d.y-24} ${d.x}, ${d.y} ${d.x}`;
    } else {
      return `M ${s.x} ${s.y} C ${s.x} ${(s.y + d.y) / 2}, ${d.x} ${(s.y + d.y) / 2}, ${d.x} ${d.y}`;
    }
  }
}
