import { truncate } from '../utils/DataTransformers.js';

export class GraphRenderer {
  constructor({ root }){ this.rootSel = root; this.zoom = null; }
  setData(data){ this.data = data; }

  layout(){
    const nodes = []; const links = [];
    const laneMap = new Map(); let lane = 0;
    function walk(node, parent){
      if(!laneMap.has(node.id)) laneMap.set(node.id, laneMap.has(node.parentId) ? laneMap.get(node.parentId) : (parent ? laneMap.get(parent.id) : (lane++)));
      const n = { id: node.id, t: node.transcription||'', name: node.name, parentId: node.parentId, lane: laneMap.get(node.id), data: node };
      nodes.push(n); if(parent) links.push({ source: parent.id, target: node.id });
      (node.children||[]).forEach(c=> walk(c, node));
    }
    (this.data.roots||[]).forEach(r=> walk(r,null));
    nodes.sort((a,b)=> a.id-b.id);
    const rowH=46; nodes.forEach((n,i)=> n.y = 24 + i*rowH);
    const laneGap=26; const x0=140; nodes.forEach(n=> n.x = x0 + n.lane*laneGap);
    links.forEach(l=> { l.s = nodes.find(n=>n.id===l.source); l.t = nodes.find(n=>n.id===l.target); });
    this.nodes = nodes; this.links = links;
  }

  setup(){
    this.layout();
    this.svg = d3.select(this.rootSel).append('svg').attr('width','100%').attr('height','100%');
    this.g = this.svg.append('g');
    this.zoom = d3.zoom().on('zoom', ev=> this.g.attr('transform', ev.transform));
    this.svg.call(this.zoom);
    this.resize(); window.addEventListener('resize', ()=> this.resize());
  }

  resize(){ const el = document.querySelector(this.rootSel); const width = Math.max(el.clientWidth, 800); const height = Math.max(el.clientHeight, (this.nodes?.length||1)*46 + 60); this.svg.attr('viewBox', `0 0 ${width} ${height}`); }

  render(){ if(!this.svg) this.setup();
    const lanes = d3.group(this.nodes, d=> d.lane);
    this.g.selectAll('.rail').data([...lanes.keys()]).join('line')
      .attr('class','rail').attr('x1', d=> 140 + d*26).attr('x2', d=> 140 + d*26).attr('y1',0).attr('y2',10000).attr('stroke','#5a6b85').attr('opacity',0.6);

    this.g.selectAll('.link-path').data(this.links).join('path')
      .attr('class','link-path').attr('d', l=>`M ${l.s.x} ${l.s.y} C ${l.s.x+24} ${l.s.y}, ${l.t.x-24} ${l.t.y}, ${l.t.x} ${l.t.y}`).attr('stroke','#5a6b85').attr('fill','none');

    const row = this.g.selectAll('.node-row').data(this.nodes, d=> d.id).join('g').attr('class','node-row').attr('transform', d=>`translate(${d.x},${d.y})`);
    row.append('circle').attr('class','node-dot').attr('r',6).attr('fill', d=> ['#7c5cff','#4cc9f0','#f72585','#f1c40f','#2ecc71','#e67e22','#1abc9c'][d.lane%7]);
    const content = row.append('g').attr('transform','translate(14,0)');
    content.append('text').attr('class','wip-text').attr('dy','0.35em').text(d=> truncate(d.t, 120));
  }

  fit(){ const el = document.querySelector(this.rootSel); const vb = this.svg.attr('viewBox').split(' ').map(Number); const kx = el.clientWidth / vb[2]; const ky = el.clientHeight / vb[3]; const k = Math.min(kx, ky); this.svg.transition().duration(400).call(this.zoom.transform, d3.zoomIdentity.scale(k)); }
}
