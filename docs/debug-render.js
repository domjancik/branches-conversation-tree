const puppeteer = require('puppeteer');

async function debugRender() {
    console.log('🔍 Starting render debug...');
    
    const browser = await puppeteer.launch({
        headless: false, // Show browser so we can see what's happening
        args: ['--no-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 800 });
    
    // Listen to console logs from the page
    page.on('console', msg => {
        console.log(`[PAGE] ${msg.text()}`);
    });
    
    // Listen to page errors
    page.on('pageerror', err => {
        console.error(`[PAGE ERROR] ${err.message}`);
    });
    
    console.log('📖 Loading page...');
    await page.goto('http://localhost:3001/index.html?nopaged', {
        waitUntil: 'networkidle0',
        timeout: 10000
    });
    
    // Wait a bit for dynamic content
    await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 2000)));
    
    // Check what's in the content element
    const contentInfo = await page.evaluate(() => {
        const content = document.getElementById('content');
        if (!content) return { exists: false };
        
        return {
            exists: true,
            innerHTML: content.innerHTML.substring(0, 500) + '...',
            textContent: content.textContent.substring(0, 200) + '...',
            childCount: content.children.length,
            hasMarkdownBody: !!content.querySelector('.markdown-body'),
            markdownBodyChildCount: content.querySelector('.markdown-body')?.children?.length || 0,
            firstChild: content.firstElementChild?.tagName,
            isVisible: window.getComputedStyle(content).display !== 'none' && 
                       window.getComputedStyle(content).visibility !== 'hidden'
        };
    });
    
    console.log('📊 Content analysis:', JSON.stringify(contentInfo, null, 2));
    
    // Check TOC
    const tocInfo = await page.evaluate(() => {
        const toc = document.getElementById('toc');
        return {
            exists: !!toc,
            innerHTML: toc?.innerHTML.substring(0, 300) || 'N/A',
            childCount: toc?.children?.length || 0
        };
    });
    
    console.log('📋 TOC analysis:', JSON.stringify(tocInfo, null, 2));
    
    // Take a screenshot
    await page.screenshot({ 
        path: 'debug-screenshot.png',
        fullPage: true 
    });
    console.log('📸 Screenshot saved as debug-screenshot.png');
    
    // Keep browser open for 5 seconds so you can inspect
    console.log('🔍 Browser will stay open for 5 seconds for inspection...');
    await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 5000)));
    
    await browser.close();
    console.log('✅ Debug complete');
}

debugRender().catch(console.error);
