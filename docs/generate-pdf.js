/**
 * PDF Generation Script
 * Generates beautiful PDF from the documentation using Puppeteer
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

class PDFGenerator {
    constructor() {
        this.browser = null;
        this.page = null;
    }

    async init() {
        console.log('🚀 Starting PDF generation...');
        
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--allow-file-access-from-files'
            ]
        });

        this.page = await this.browser.newPage();
        
        // Set a larger viewport for better rendering
        await this.page.setViewport({
            width: 1200,
            height: 1600,
            deviceScaleFactor: 2
        });
    }

    async generatePDF() {
        try {
            const htmlPath = path.resolve(__dirname, 'index.html');
            const outputPath = path.resolve(__dirname, '../PROJECT_SPECIFICATION.pdf');
            
            console.log('📄 Loading HTML document...');
            await this.page.goto(`file://${htmlPath}`, {
                waitUntil: 'networkidle0',
                timeout: 60000
            });

            // Wait for Paged.js to finish processing
            console.log('⏳ Waiting for Paged.js to complete...');
            await this.waitForPagedJS();

            // Give extra time for any animations or final processing
            await this.page.waitForTimeout(2000);

            console.log('🎨 Generating PDF with beautiful formatting...');
            
            // Generate PDF with print media type
            await this.page.emulateMediaType('print');
            
            const pdfBuffer = await this.page.pdf({
                path: outputPath,
                format: 'A4',
                margin: {
                    top: '2.5cm',
                    right: '2cm',
                    bottom: '2cm',
                    left: '2cm'
                },
                printBackground: true,
                displayHeaderFooter: false, // We handle this with CSS
                preferCSSPageSize: true,
                timeout: 60000
            });

            console.log('✅ PDF generated successfully!');
            console.log(`📍 Output: ${outputPath}`);
            
            // Get file size for reporting
            const stats = fs.statSync(outputPath);
            const fileSizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
            console.log(`📊 File size: ${fileSizeInMB} MB`);

            return outputPath;

        } catch (error) {
            console.error('❌ Error generating PDF:', error);
            throw error;
        }
    }

    async waitForPagedJS() {
        // Wait for Paged.js to complete pagination
        await this.page.waitForFunction(() => {
            return window.PagedPolyfill && window.PagedPolyfill.isReady;
        }, { timeout: 30000 });

        // Additional wait for any dynamic content
        await this.page.waitForTimeout(3000);

        // Check if there are any error messages in the console
        const errorMessages = await this.page.evaluate(() => {
            const errors = [];
            const errorBoxes = document.querySelectorAll('.warning-box, .error-box');
            errorBoxes.forEach(box => {
                errors.push(box.textContent);
            });
            return errors;
        });

        if (errorMessages.length > 0) {
            console.warn('⚠️  Warning messages found in document:');
            errorMessages.forEach(msg => console.warn('   ', msg));
        }

        // Get page count
        const pageCount = await this.page.evaluate(() => {
            const pages = document.querySelectorAll('.pagedjs_page');
            return pages.length;
        });

        console.log(`📄 Document has ${pageCount} pages`);
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    async generate() {
        try {
            await this.init();
            const outputPath = await this.generatePDF();
            return outputPath;
        } finally {
            await this.cleanup();
        }
    }
}

// CLI usage
if (require.main === module) {
    const generator = new PDFGenerator();
    
    generator.generate()
        .then(outputPath => {
            console.log('\n🎉 PDF Generation Complete!');
            console.log(`📖 Your beautiful documentation is ready: ${path.basename(outputPath)}`);
            console.log('\n💡 Tips:');
            console.log('   • Open the PDF in your favorite PDF viewer');
            console.log('   • The document is optimized for printing on A4 paper');
            console.log('   • All code blocks and diagrams should be crisp and readable');
            process.exit(0);
        })
        .catch(error => {
            console.error('\n💥 PDF generation failed:', error.message);
            process.exit(1);
        });
}

module.exports = PDFGenerator;
