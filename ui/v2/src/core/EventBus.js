export class EventBus {
  constructor(){ this.handlers = new Map(); }
  on(evt, fn){
    if(!this.handlers.has(evt)) this.handlers.set(evt, new Set());
    this.handlers.get(evt).add(fn);
  }
  off(evt, fn){ this.handlers.get(evt)?.delete(fn); }
  emit(evt, payload){ this.handlers.get(evt)?.forEach(fn=> fn(payload)); }
}
