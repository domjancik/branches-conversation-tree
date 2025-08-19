export class ControlsPanel {
  constructor({ selectors, state, bus }){
    this.state = state; this.bus = bus; this.sel = selectors;
  }
  init(){
    document.querySelector(this.sel.resetZoom).addEventListener('click', ()=> this.bus.emit('tree:resetZoom'));
    document.querySelector(this.sel.expandAll).addEventListener('click', ()=> this.bus.emit('tree:expandAll'));
    document.querySelector(this.sel.collapseAll).addEventListener('click', ()=> this.bus.emit('tree:collapseAll'));
    document.querySelector(this.sel.layoutToggle).addEventListener('click', ()=> this.bus.emit('layout:toggle'));
    document.querySelector(this.sel.rootSelector).addEventListener('change', (e)=> this.bus.emit('root:change', parseInt(e.target.value)));
  }
  populateRoots(roots){
    const sel = document.querySelector(this.sel.rootSelector);
    while(sel.children.length>1) sel.removeChild(sel.lastChild);
    roots.forEach((r, i)=>{ const o = document.createElement('option'); o.value = i; o.textContent = r.name; if(i===0) o.selected=true; sel.appendChild(o); });
  }
}
