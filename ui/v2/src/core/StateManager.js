export class StateManager {
  constructor(bus){
    this.bus = bus;
    this.state = new Map([
      ['layout', 'vertical'],
      ['selectedNode', null],
      ['config', {}],
      ['data', null],
      ['rootIndex', 0]
    ]);
  }
  get(k){ return this.state.get(k); }
  set(k,v){ this.state.set(k,v); this.bus.emit(`state:${k}`, v); }
}
