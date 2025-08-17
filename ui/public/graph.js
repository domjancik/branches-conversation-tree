// Graph view rendering of recordings as git-branch-like lanes
(function(){
  const margin = { top: 24, right: 24, bottom: 24, left: 140 };
  let width = 0, height = 0;
  let svg, g, zoom;
  let data, nodes = [], links = [];

  async function init(){
    await loadTree();
    layout();
    setupSvg();
    render();
    bindUI();
  }

  async function loadTree(){
    const res = await fetch('/api/tree-data');
    data = await res.json();
  }

  function flattenRoots(roots){
    // produce array of nodes with branch lane index based on root id
    const laneMap = new Map();
    let lane = 0;
    function walk(node, parent){
      if(!laneMap.has(node.id)) laneMap.set(node.id, laneMap.has(node.parentId) ? laneMap.get(node.parentId) : (parent ? laneMap.get(parent.id) : (lane++)));
      const n = { id: node.id, t: node.transcription || '', name: node.name, parentId: node.parentId, lane: laneMap.get(node.id), data: node };
      nodes.push(n);
      if(parent) links.push({ source: parent.id, target: node.id });
      (node.children||[]).forEach(child=>walk(child, node));
    }
    roots.forEach(r=>walk(r, null));
  }

  function layout(){
    nodes = []; links = [];
    flattenRoots(data.roots || []);
    // vertical spacing per commit row
    const rowH = 46; // space for text + thumbs
    nodes.sort((a,b)=>a.id-b.id); // simple order by id for now
    nodes.forEach((n,i)=>{ n.y = margin.top + i*rowH; });
    // lane x positions
    const laneWidth = 18; const laneGap = 26;
    const x0 = margin.left;
    const laneX = (lane)=> x0 + lane*laneGap;
    nodes.forEach(n=>{ n.x = laneX(n.lane); });
    links.forEach(l=>{
      const s = nodes.find(n=>n.id===l.source);
      const t = nodes.find(n=>n.id===l.target);
      l.s = s; l.t = t;
    });
    const rows = nodes.length;
    height = Math.max(rows*rowH + margin.top + margin.bottom, window.innerHeight-44);
    width = Math.max(margin.left + (Math.max(...nodes.map(n=>n.lane))+1)*laneGap + 800, window.innerWidth);
  }

  function setupSvg(){
    svg = d3.select('#graph').append('svg')
      .attr('width','100%').attr('height','100%');
    g = svg.append('g');
    zoom = d3.zoom().on('zoom', (ev)=> g.attr('transform', ev.transform));
    svg.call(zoom);
    resize();
    window.addEventListener('resize', resize);
  }

  function resize(){
    const el = document.getElementById('graph');
    svg.attr('viewBox', `0 0 ${Math.max(el.clientWidth, width)} ${Math.max(el.clientHeight, height)}`);
  }

  async function render(){
    // rails per lane (vertical lines)
    const lanes = d3.group(nodes, d=>d.lane);
    const laneWidth = 26;
    g.selectAll('.rail').data([...lanes.keys()])
      .join('line')
      .attr('class','rail')
      .attr('x1', d=>margin.left + d*laneWidth)
      .attr('x2', d=>margin.left + d*laneWidth)
      .attr('y1', 0)
      .attr('y2', height)
      .attr('stroke', getCss('--rail'))
      .attr('stroke-width',1.5)
      .attr('opacity',0.6);

    // links
    g.selectAll('.link-path').data(links)
      .join('path')
      .attr('class','link-path')
      .attr('d', l=>`M ${l.s.x} ${l.s.y} C ${l.s.x+24} ${l.s.y}, ${l.t.x-24} ${l.t.y}, ${l.t.x} ${l.t.y}`);

    // rows
    const row = g.selectAll('.node-row').data(nodes, d=>d.id).join('g').attr('class','node-row');
    row.attr('transform', d=>`translate(${d.x},${d.y})`);

    row.append('circle').attr('class','node-dot')
      .attr('r',6).attr('fill', laneColor);

    // transcription text and thumbs to the right
    const content = row.append('g').attr('transform','translate(14,0)');
    content.append('text').attr('class','wip-text').attr('dy','0.35em')
      .text(d=>truncate(d.t, 120));

    // thumbnails
    content.each(async function(d){
      const group = d3.select(this).append('g').attr('class','thumb-group').attr('transform','translate(520,-14)');
      const imgs = await fetch(`/api/recordings/${d.id}/images`).then(r=>r.json()).catch(()=>[]);
      imgs.slice(0,6).forEach((img, i)=>{
        group.append('image')
          .attr('href', `/images/${encodeURIComponent(img.image_file_path)}`)
          .attr('x', i*34)
          .attr('width', 28)
          .attr('height', 28)
          .on('error', function(){ d3.select(this).remove(); });
      });
    });
  }

  function getCss(varName){
    return getComputedStyle(document.documentElement).getPropertyValue(varName) || '#3b4b63';
  }
  function laneColor(d){
    const colors = ['#7c5cff','#4cc9f0','#f72585','#f1c40f','#2ecc71','#e67e22','#1abc9c'];
    return colors[d.lane % colors.length];
  }
  function truncate(s,n){ return s && s.length>n ? s.slice(0,n-1)+'…' : (s||''); }

  function bindUI(){
    document.getElementById('fit').addEventListener('click', ()=>{
      const el = document.getElementById('graph');
      const vb = svg.attr('viewBox').split(' ').map(Number);
      const kx = el.clientWidth / vb[2];
      const ky = el.clientHeight / vb[3];
      const k = Math.min(kx, ky);
      svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity.scale(k));
    });
    document.getElementById('toggleTheme').addEventListener('click', ()=>{
      document.body.classList.toggle('light');
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();

