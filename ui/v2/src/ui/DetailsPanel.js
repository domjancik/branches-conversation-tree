export class DetailsPanel {
  constructor(selector){ this.root = document.querySelector(selector); }
  render(node){
    const fmtDate = (s)=> s ? new Date(s).toLocaleString() : 'N/A';
    const fmtDur = (d)=> (d||d===0) ? `${Number(d).toFixed(2)}s` : 'N/A';
    this.root.innerHTML = `
      <h3>${node.name}</h3>
      <div class="detail-item"><span class="detail-label">ID:</span> <span>${node.id}</span></div>
      <div class="detail-item"><span class="detail-label">Duration:</span> <span>${fmtDur(node.duration)}</span></div>
      <div class="detail-item"><span class="detail-label">Created:</span> <span>${fmtDate(node.createdDate)}</span></div>
      <div class="detail-item"><span class="detail-label">Parent:</span> <span>${node.parentId || 'Root'}</span></div>
      ${node.parentTime ? `<div class="detail-item"><span class="detail-label">Branch Time:</span> <span>${fmtDur(node.parentTime)}</span></div>` : ''}
      ${node.transcription ? `<div class="transcription-text">${node.transcription}</div>` : ''}
    `;
  }
}
