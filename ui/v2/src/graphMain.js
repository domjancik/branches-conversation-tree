import { ApiService } from './services/ApiService.js';
import { GraphRenderer } from './visualization/GraphRenderer.js';

const api = new ApiService();
let originalData = null;
let renderer = null;

async function init(){
  originalData = await api.loadTreeData();
  renderer = new GraphRenderer({ root: '#graph' });
  populateRoots(originalData.roots || []);
  bindUI();
  updateView();
}

function populateRoots(roots){
  const sel = document.getElementById('rootSelector');
  // preserve first placeholder option
  while(sel.children.length > 1) sel.removeChild(sel.lastChild);
  roots.forEach((r, i)=>{
    const opt = document.createElement('option');
    opt.value = String(i);
    opt.textContent = r.name || `Root ${i+1}`;
    sel.appendChild(opt);
  });
}

function currentFilter(){
  const unfiltered = document.getElementById('unfiltered').checked;
  const idxStr = document.getElementById('rootSelector').value;
  const index = idxStr === '' ? null : parseInt(idxStr,10);
  return { unfiltered, index };
}

function filteredData(){
  const { unfiltered, index } = currentFilter();
  if (unfiltered || index === null || isNaN(index)) return originalData;
  const roots = originalData.roots || [];
  if (index < 0 || index >= roots.length) return originalData;
  return { ...originalData, roots: [ roots[index] ] };
}

function updateView(){
  const data = filteredData();
  renderer.setData(data);
  renderer.render();
}

function bindUI(){
  document.getElementById('fit')?.addEventListener('click', ()=> renderer.fit());
  document.getElementById('toggleTheme')?.addEventListener('click', ()=> document.body.classList.toggle('light'));
  const unfiltered = document.getElementById('unfiltered');
  const rootSelector = document.getElementById('rootSelector');
  unfiltered.addEventListener('change', ()=>{
    rootSelector.disabled = unfiltered.checked;
    updateView();
  });
  rootSelector.addEventListener('change', ()=> updateView());
}

document.addEventListener('DOMContentLoaded', init);
