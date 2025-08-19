export class LayoutManager {
  constructor(state, bus){ this.state = state; this.bus = bus; }
  toggle(){
    const cur = this.state.get('layout');
    const next = cur === 'vertical' ? 'horizontal' : 'vertical';
    this.state.set('layout', next);
    const btn = document.getElementById('layoutToggle');
    if(btn) btn.textContent = next === 'vertical' ? 'Horizontal Layout' : 'Vertical Layout';
  }
}
