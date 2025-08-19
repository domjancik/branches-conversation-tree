export const qs = (sel, root=document) => root.querySelector(sel);
export const on = (el, evt, fn) => el.addEventListener(evt, fn);
