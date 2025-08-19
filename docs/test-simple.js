const puppeteer = require('puppeteer');

async function testSimplePage() {
    const browser = await puppeteer.launch({ headless: false });
    
    try {
        const page = await browser.newPage();
        
        // Listen to console messages from the page
        page.on('console', (msg) => {
            console.log(`[PAGE] ${msg.type()}: ${msg.text()}`);
        });
        
        const url = 'http://127.0.0.1:3001/debug-simple.html';
        console.log(`🔗 Loading: ${url}`);
        
        await page.goto(url, { waitUntil: 'networkidle0' });
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
        
        // Check final results
        const results = await page.evaluate(() => {
            const debugEl = document.getElementById('debug-info');
            const contentEl = document.getElementById('content');
            
            return {
                debugHTML: debugEl ? debugEl.innerHTML : 'No debug element',
                contentLength: contentEl ? contentEl.innerHTML.length : 0,
                contentText: contentEl ? contentEl.textContent.trim().substring(0, 200) : 'No content',
                hasContent: contentEl && contentEl.innerHTML.length > 1000
            };
        });
        
        console.log('\n=== TEST RESULTS ===');
        console.log('Content length:', results.contentLength);
        console.log('Has substantial content:', results.hasContent);
        console.log('Content preview:', results.contentText);
        
        if (results.hasContent) {
            console.log('✅ SUCCESS: Basic loading works!');
        } else {
            console.log('❌ FAILURE: Basic loading failed');
        }
        
        // Keep browser open for a bit to see results
        console.log('\nBrowser will close in 10 seconds...');
        setTimeout(() => browser.close(), 10000);
        
    } catch (error) {
        console.error('❌ Error:', error);
        await browser.close();
    }
}

testSimplePage();
