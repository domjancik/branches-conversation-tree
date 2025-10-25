const topicColors = {};
const colorPalette = [
  '#e6194b', '#3cb44b', '#ffe119', '#0082c8', '#f58231',
  '#911eb4', '#46f0f0', '#f032e6', '#d2f53c', '#fabebe',
  '#008080', '#e6beff', '#aa6e28', '#fffac8', '#800000',
  '#aaffc3', '#808000', '#ffd8b1', '#000080', '#808080'
];

function assignColor(topic) {
  if (!topicColors[topic]) {
    const idx = Object.keys(topicColors).length % colorPalette.length;
    topicColors[topic] = colorPalette[idx];
  }
  return topicColors[topic];
}

function renderTranscript(text, segments) {
  const ranges = [];
  segments.forEach(seg => {
    const color = assignColor(seg.category || seg.topic || 'unknown');
    (seg.text_ranges || []).forEach(r => {
      if (typeof r.start_char === 'number' && typeof r.end_char === 'number') {
        ranges.push({ start: r.start_char, end: r.end_char, color });
      }
    });
  });
  ranges.sort((a, b) => a.start - b.start);

  const container = document.getElementById('transcript');
  container.innerHTML = '';

  let cursor = 0;
  ranges.forEach(r => {
    if (cursor < r.start) {
      const span = document.createElement('span');
      span.textContent = text.slice(cursor, r.start);
      container.appendChild(span);
    }
    const span = document.createElement('span');
    span.textContent = text.slice(r.start, r.end);
    span.style.borderBottom = `4px solid ${r.color}`;
    span.style.paddingBottom = '2px';
    container.appendChild(span);
    cursor = r.end;
  });
  if (cursor < text.length) {
    const span = document.createElement('span');
    span.textContent = text.slice(cursor);
    container.appendChild(span);
  }
}

function loadData(data) {
  const jsonEl = document.getElementById('json');
  jsonEl.textContent = JSON.stringify(data, null, 2);

  const transcript = data.metadata?.transcript || '';
  const segments = data.result?.segments || [];
  renderTranscript(transcript, segments);
}

export { loadData };
