export class TooltipManager {
  constructor(){
    this.el = document.createElement('div');
    this.el.className = 'tooltip';
    this.el.style.opacity = 0;
    document.body.appendChild(this.el);
  }
  show(html, x, y){
    this.el.innerHTML = html; this.el.style.left = (x+10)+'px'; this.el.style.top = (y-28)+'px'; this.el.style.opacity = 0.95;
  }
  hide(){ this.el.style.opacity = 0; }
}
