export class ConfigService {
  set(cfg){ this.cfg = cfg; }
  get(){ return this.cfg || { defaultRootIndex:0, maxNodeTextLength:20, animationDuration:750, nodeRadius:8, treeMargin:{top:40,right:40,bottom:40,left:40} }; }
}
