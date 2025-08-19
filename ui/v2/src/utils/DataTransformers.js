export const truncate = (text, n) => (text && text.length>n) ? text.slice(0, n)+'…' : (text||'');
