#!/usr/bin/env node

/**
 * Audit rendered sections against source markdown
 * - Reads docs/PROJECT_SPECIFICATION.md
 * - Loads http://127.0.0.1:3001/index.html?nopaged
 * - Compares content length per section between markdown and rendered DOM
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const DOCS_DIR = __dirname;
const SRC_MD = path.join(DOCS_DIR, 'PROJECT_SPECIFICATION.md');
const URL = 'http://127.0.0.1:3001/index.html?nopaged';

function parseMarkdownSections(md) {
  const lines = md.split(/\r?\n/);
  const sections = [];
  let current = null;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const m = /^(#{1,6})\s+(.+?)\s*$/.exec(line);
    if (m) {
      if (current) {
        current.text = current.buffer.join('\n').trim();
        current.length = current.text.length;
        sections.push(current);
      }
      current = { level: m[1].length, title: m[2].trim(), startLine: i + 1, buffer: [] };
    } else if (current) {
      current.buffer.push(line);
    }
  }
  if (current) {
    current.text = current.buffer.join('\n').trim();
    current.length = current.text.length;
    sections.push(current);
  }
  return sections;
}

(async () => {
  if (!fs.existsSync(SRC_MD)) {
    console.error('Missing source markdown:', SRC_MD);
    process.exit(1);
  }
  const md = fs.readFileSync(SRC_MD, 'utf8');
  const srcSections = parseMarkdownSections(md);
  console.log(`Source sections: ${srcSections.length}`);

  const browser = await puppeteer.launch({ headless: 'new' });
  try {
    const page = await browser.newPage();
    page.on('console', (msg) => console.log('[BROWSER]', msg.type(), msg.text()));
    await page.goto(URL, { waitUntil: 'networkidle0' });
    // wait a bit for renderer
    await page.waitForSelector('#content .markdown-body', { timeout: 10000 });

    const rendered = await page.evaluate(() => {
      const result = [];
      const content = document.querySelector('#content');
      const headings = content ? content.querySelectorAll('h1, h2, h3, h4, h5, h6') : [];
      const getLevel = (h) => parseInt(h.tagName.substring(1));
      for (let i = 0; i < headings.length; i++) {
        const h = headings[i];
        const level = getLevel(h);
        const title = (h.textContent || '').trim();
        let node = h.nextSibling;
        let text = '';
        let html = '';
        while (node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const tag = node.tagName.toLowerCase();
            if (/^h[1-6]$/.test(tag)) {
              const nextLevel = parseInt(tag.substring(1));
              if (nextLevel <= level) break; // end of this section
            }
            text += (node.textContent || '').trim() + '\n';
            html += node.outerHTML || '';
          } else if (node.nodeType === Node.TEXT_NODE) {
            text += (node.textContent || '').trim();
          }
          node = node.nextSibling;
        }
        result.push({ title, level, textLength: text.trim().length, hasHTML: html.trim().length > 0 });
      }
      return result;
    });

    // Try to match by title to compare lengths
    function normalizeTitle(t) {
      return t.toLowerCase().replace(/\s+/g, ' ').replace(/[\.:]/g, '').trim();
    }
    const srcMap = new Map();
    srcSections.forEach(s => srcMap.set(normalizeTitle(s.title), s));

    const report = [];
    for (const r of rendered) {
      const key = normalizeTitle(r.title);
      const src = srcMap.get(key);
      if (!src) continue;
      // consider a section "missing" if the source length >= 50 chars but rendered length < 10
      if (src.length >= 50 && r.textLength < 10) {
        report.push({ title: r.title, level: r.level, sourceLen: src.length, renderedLen: r.textLength });
      }
    }

    if (report.length === 0) {
      console.log('All headings have content rendered (thresholded check).');
    } else {
      console.log('\nSections with missing/near-empty rendered content:');
      report.forEach(r => {
        console.log(`- ${'#'.repeat(r.level)} ${r.title} | source: ${r.sourceLen}, rendered: ${r.renderedLen}`);
      });
    }

  } catch (e) {
    console.error('Audit failed:', e);
  } finally {
    await browser.close();
  }
})();

