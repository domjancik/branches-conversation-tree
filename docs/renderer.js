/**
 * Beautiful Documentation Renderer
 * Transforms PROJECT_SPECIFICATION.md into a stunning print-ready document
 */

class DocumentRenderer {
    constructor() {
        this.headings = [];
        this.currentPageNumber = 1;
        this.tocEntries = [];
        
        // Configure marked.js
        marked.setOptions({
            highlight: function(code, lang) {
                if (Prism.languages[lang]) {
                    return Prism.highlight(code, Prism.languages[lang], lang);
                }
                return code;
            },
            breaks: true,
            gfm: true
        });
    }

    async init() {
        try {
            await this.loadMarkdown();
            this.generateTOC();
            this.enhanceContent();
            this.setupPagedJS();
        } catch (error) {
            console.error('Error initializing document:', error);
            this.showError(error);
        }
    }

    async loadMarkdown() {
        try {
            // Try to load from the parent directory
            const response = await fetch('../PROJECT_SPECIFICATION.md');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const markdown = await response.text();
            const html = marked.parse(markdown);
            const sanitizedHtml = DOMPurify.sanitize(html);
            
            document.getElementById('content').innerHTML = sanitizedHtml;
        } catch (error) {
            console.warn('Could not load from parent directory, trying local copy');
            // Fallback: show instructions to copy the file
            this.showCopyInstructions();
        }
    }

    showCopyInstructions() {
        document.getElementById('content').innerHTML = `
            <div class="info-box" style="margin: 2rem 0; text-align: center;">
                <h2>Setup Required</h2>
                <p>To render the documentation, please copy your <code>PROJECT_SPECIFICATION.md</code> file to the <code>docs</code> directory, or run a local server from the project root.</p>
                <p>Alternatively, run: <code>npm run dev</code> from the docs directory.</p>
            </div>
        `;
    }

    showError(error) {
        document.getElementById('content').innerHTML = `
            <div class="warning-box" style="margin: 2rem 0;">
                <h2>Error Loading Document</h2>
                <p>There was an error loading the PROJECT_SPECIFICATION.md file:</p>
                <code>${error.message}</code>
                <p>Please ensure the file exists and is accessible.</p>
            </div>
        `;
    }

    generateTOC() {
        const content = document.getElementById('content');
        const headings = content.querySelectorAll('h1, h2, h3');
        const tocContainer = document.getElementById('toc');
        
        this.tocEntries = [];
        
        headings.forEach((heading, index) => {
            // Generate ID if it doesn't exist
            if (!heading.id) {
                heading.id = this.generateId(heading.textContent);
            }
            
            const level = parseInt(heading.tagName.substring(1));
            const tocEntry = {
                level,
                id: heading.id,
                text: heading.textContent,
                element: heading
            };
            
            this.tocEntries.push(tocEntry);
        });

        // Generate TOC HTML
        const tocHtml = this.tocEntries.map(entry => {
            return `
                <div class="toc-entry level-${entry.level}">
                    <span class="toc-title-text">${entry.text}</span>
                    <span class="toc-page-number">${entry.pageNumber || '...'}</span>
                </div>
            `;
        }).join('');

        tocContainer.innerHTML = tocHtml;
    }

    generateId(text) {
        return text
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    enhanceContent() {
        const content = document.getElementById('content');
        
        // Enhance code blocks
        this.enhanceCodeBlocks(content);
        
        // Enhance tables
        this.enhanceTables(content);
        
        // Add page break hints
        this.addPageBreakHints(content);
        
        // Process mermaid diagrams if any
        this.processMermaidDiagrams(content);
        
        // Enhance interface definitions
        this.enhanceInterfaceDefinitions(content);
    }

    enhanceCodeBlocks(content) {
        const codeBlocks = content.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            block.parentElement.classList.add('avoid-break');
            
            // Add language label if detected
            const className = block.className;
            const langMatch = className.match(/language-(\w+)/);
            if (langMatch) {
                const langLabel = document.createElement('div');
                langLabel.className = 'code-language';
                langLabel.textContent = langMatch[1].toUpperCase();
                langLabel.style.cssText = `
                    position: absolute;
                    top: 0.5rem;
                    right: 0.5rem;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 0.2rem 0.5rem;
                    border-radius: 3px;
                    font-size: 0.7em;
                    font-weight: 600;
                `;
                block.parentElement.style.position = 'relative';
                block.parentElement.appendChild(langLabel);
            }
        });
    }

    enhanceTables(content) {
        const tables = content.querySelectorAll('table');
        tables.forEach(table => {
            table.classList.add('avoid-break');
            
            // Wrap table in a container
            const wrapper = document.createElement('div');
            wrapper.className = 'table-wrapper';
            wrapper.style.cssText = `
                overflow-x: auto;
                margin: 1.5rem 0;
                border: 1px solid var(--border-light);
                border-radius: 6px;
            `;
            
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    addPageBreakHints(content) {
        const h1Elements = content.querySelectorAll('h1');
        h1Elements.forEach((h1, index) => {
            if (index > 0) {
                h1.classList.add('page-break');
            }
            h1.classList.add('keep-with-next');
        });

        const h2Elements = content.querySelectorAll('h2');
        h2Elements.forEach(h2 => {
            h2.classList.add('keep-with-next');
        });
    }

    processMermaidDiagrams(content) {
        // Look for mermaid code blocks and convert them
        const mermaidBlocks = content.querySelectorAll('pre code.language-mermaid');
        mermaidBlocks.forEach(block => {
            const mermaidDiv = document.createElement('div');
            mermaidDiv.className = 'mermaid avoid-break';
            mermaidDiv.textContent = block.textContent;
            
            block.parentElement.parentElement.insertBefore(mermaidDiv, block.parentElement);
            block.parentElement.remove();
        });
    }

    enhanceInterfaceDefinitions(content) {
        // Find TypeScript interface definitions and enhance them
        const codeBlocks = content.querySelectorAll('pre code.language-typescript');
        codeBlocks.forEach(block => {
            const code = block.textContent;
            if (code.includes('interface ') || code.includes('enum ') || code.includes('class ')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'interface-definition avoid-break';
                
                const header = document.createElement('div');
                header.className = 'interface-header';
                
                // Extract interface/enum/class name
                const match = code.match(/(?:interface|enum|class)\s+(\w+)/);
                if (match) {
                    header.textContent = `${match[0]}`;
                } else {
                    header.textContent = 'Type Definition';
                }
                
                const body = document.createElement('div');
                body.className = 'interface-body';
                body.appendChild(block.parentElement.cloneNode(true));
                
                wrapper.appendChild(header);
                wrapper.appendChild(body);
                
                block.parentElement.parentElement.insertBefore(wrapper, block.parentElement);
                block.parentElement.remove();
            }
        });
    }

    setupPagedJS() {
        // Configure Paged.js hooks
        class MyHandler extends Paged.Handler {
            constructor(chunker, polisher, caller) {
                super(chunker, polisher, caller);
            }

            beforeParsed(content) {
                console.log('Document parsing started...');
            }

            afterParsed(parsed) {
                console.log('Document parsed successfully');
            }

            beforePageLayout(page, contents, renderTo, pageNumber) {
                // Update TOC page numbers
                this.updateTOCPageNumbers(pageNumber);
            }

            afterPageLayout(pageElement, page, breakToken, pageNumber) {
                console.log(`Page ${pageNumber} laid out`);
            }

            afterRendered(pages) {
                console.log(`Document rendered with ${pages.length} pages`);
                this.finalizeDocument(pages.length);
            }

            updateTOCPageNumbers(currentPage) {
                // This is a simplified version - in practice you'd need more sophisticated
                // page number tracking for TOC entries
            }

            finalizeDocument(totalPages) {
                // Add any final touches
                console.log(`✅ Beautiful documentation ready! ${totalPages} pages generated.`);
                
                // Show completion message in dev mode
                if (window.location.protocol === 'http:') {
                    setTimeout(() => {
                        this.showCompletionMessage(totalPages);
                    }, 1000);
                }
            }

            showCompletionMessage(totalPages) {
                const message = document.createElement('div');
                message.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    font-family: var(--font-secondary);
                    font-weight: 600;
                    z-index: 1000;
                    animation: slideIn 0.5s ease-out;
                `;
                
                message.innerHTML = `
                    ✨ Document Ready!<br>
                    <small style="opacity: 0.9">${totalPages} pages • Press Ctrl+P to print</small>
                `;

                // Add animation keyframes
                if (!document.getElementById('completion-animation')) {
                    const style = document.createElement('style');
                    style.id = 'completion-animation';
                    style.textContent = `
                        @keyframes slideIn {
                            from { transform: translateX(100%); opacity: 0; }
                            to { transform: translateX(0); opacity: 1; }
                        }
                    `;
                    document.head.appendChild(style);
                }

                document.body.appendChild(message);

                // Remove after 5 seconds
                setTimeout(() => {
                    message.style.animation = 'slideIn 0.5s ease-out reverse';
                    setTimeout(() => message.remove(), 500);
                }, 5000);
            }
        }

        // Register the handler
        Paged.registerHandlers(MyHandler);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const renderer = new DocumentRenderer();
    await renderer.init();
});

// Add some utility functions
window.printDocument = function() {
    window.print();
};

window.exportToPDF = function() {
    // This would require a server-side component or browser automation
    alert('PDF export requires running the generate-pdf.js script or using your browser\'s print to PDF function (Ctrl+P)');
};

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
});
