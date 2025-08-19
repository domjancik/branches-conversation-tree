// Simple build: copy markdown into docs for local serving
const fs = require('fs');
const path = require('path');

const src = path.resolve(__dirname, '../PROJECT_SPECIFICATION.md');
const dest = path.resolve(__dirname, './PROJECT_SPECIFICATION.md');

function copySpec() {
  try {
    if (!fs.existsSync(src)) {
      console.warn('PROJECT_SPECIFICATION.md not found in parent directory. Skipping copy.');
      return;
    }
    fs.copyFileSync(src, dest);
    console.log('Copied PROJECT_SPECIFICATION.md into docs/');
  } catch (e) {
    console.error('Failed to copy PROJECT_SPECIFICATION.md:', e.message);
  }
}

copySpec();

