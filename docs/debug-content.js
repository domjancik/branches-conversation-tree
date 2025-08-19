/**
 * Debug script for testing content loading
 * Run with: node debug-content.js
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function testContentLoading() {
    const browser = await puppeteer.launch({ 
        headless: false,  // Show browser for visual debugging
        defaultViewport: { width: 1200, height: 800 }
    });
    
    try {
        const page = await browser.newPage();
        
        // Listen to console messages from the page
        page.on('console', (msg) => {
            console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
        });
        
        // Navigate to the documentation (with nopaged to avoid Paged.js issues)
        const url = 'http://127.0.0.1:3001/index.html?nopaged';
        console.log(`🔗 Loading: ${url}`);
        
        await page.goto(url, { waitUntil: 'networkidle0' });
        
        // Wait for renderer to initialize
        await page.waitForFunction(() => {
            return document.readyState === 'complete' && 
                   window.DocumentRenderer !== undefined;
        }, { timeout: 5000 }).catch(() => {});
        
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Check content element
        const contentInfo = await page.evaluate(() => {
            const contentEl = document.getElementById('content');
            const markdownBody = contentEl?.querySelector('.markdown-body');
            
            return {
                contentExists: !!contentEl,
                contentHTML: contentEl?.innerHTML?.substring(0, 300) || '',
                contentText: contentEl?.textContent?.substring(0, 300) || '',
                hasMarkdownBody: !!markdownBody,
                markdownBodyHTML: markdownBody?.innerHTML?.substring(0, 300) || '',
                headingCount: contentEl?.querySelectorAll('h1, h2, h3')?.length || 0,
                paragraphCount: contentEl?.querySelectorAll('p')?.length || 0
            };
        });
        
        console.log('\n📊 Content Analysis:');
        console.log('Content element exists:', contentInfo.contentExists);
        console.log('Has .markdown-body wrapper:', contentInfo.hasMarkdownBody);
        console.log('Headings found:', contentInfo.headingCount);
        console.log('Paragraphs found:', contentInfo.paragraphCount);
        console.log('Content text preview:', contentInfo.contentText);
        
        // Check TOC
        const tocInfo = await page.evaluate(() => {
            const tocEl = document.getElementById('toc');
            return {
                tocExists: !!tocEl,
                tocHTML: tocEl?.innerHTML?.substring(0, 200) || '',
                tocEntries: tocEl?.querySelectorAll('.toc-entry')?.length || 0
            };
        });
        
        console.log('\n📑 TOC Analysis:');
        console.log('TOC element exists:', tocInfo.tocExists);
        console.log('TOC entries found:', tocInfo.tocEntries);
        
        // Take a screenshot
        const screenshotPath = path.join(__dirname, 'debug-screenshot-nopaged.png');
        await page.screenshot({ 
            path: screenshotPath,
            fullPage: true
        });
        console.log(`\n📸 Screenshot saved: ${screenshotPath}`);
        
        // Keep browser open for manual inspection
        console.log('\n⏸️  Browser will stay open for manual inspection. Press Ctrl+C to exit.');
        
        // Wait for user input to close
        process.stdin.setRawMode(true);
        process.stdin.resume();
        process.stdin.on('data', () => process.exit(0));
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

// Run the test
testContentLoading().catch(console.error);
