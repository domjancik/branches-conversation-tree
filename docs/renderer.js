/**
 * Beautiful Documentation Renderer
 * Transforms PROJECT_SPECIFICATION.md into a stunning print-ready document
 */

class DocumentRenderer {
    constructor() {
        this.headings = [];
        this.currentPageNumber = 1;
        this.tocEntries = [];
        
        // Configure marked.js (use global from CDN)
        const md = window.marked || marked;
        md.setOptions({
            highlight: function(code, lang) {
                if (Prism.languages[lang]) {
                    return Prism.highlight(code, Prism.languages[lang], lang);
                }
                return code;
            },
            breaks: true,
            gfm: true
        });
        this._md = md;
    }

    async init() {
        try {
            const contentLoaded = await this.loadMarkdown();
            
            if (contentLoaded) {
                console.log('[renderer] Content loaded successfully, proceeding with enhancements...');
                this.generateTOC();
                this.enhanceContent();
                
                // Only setup Paged.js if not disabled
                const params = new URLSearchParams(window.location.search);
                if (!params.has('nopaged')) {
                    // Delay Paged.js setup to allow DOM to settle
                    setTimeout(() => this.setupPagedJS(), 100);
                } else {
                    console.log('[renderer] Paged.js disabled, content ready for viewing');
                }
            } else {
                console.error('[renderer] Content loading failed');
            }
        } catch (error) {
            console.error('Error initializing document:', error);
            this.showError(error);
        }
    }

    async loadMarkdown() {
        const contentEl = document.getElementById('content');
        console.log('[renderer] Starting markdown load...');
        try {
            // First try to load from local docs directory (copied by build script)
            console.log('[renderer] Trying ./PROJECT_SPECIFICATION.md');
            let response = await fetch('./PROJECT_SPECIFICATION.md');
            console.log('[renderer] Local fetch response:', response.status, response.ok);
            if (!response.ok) {
                // Then try parent directory as a fallback (works if server serves parent)
                console.log('[renderer] Trying ../PROJECT_SPECIFICATION.md');
                response = await fetch('../PROJECT_SPECIFICATION.md');
                console.log('[renderer] Parent fetch response:', response.status, response.ok);
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            let markdown = await response.text();
            // Strip UTF-8 BOM if present
            if (markdown.charCodeAt(0) === 0xFEFF) {
                console.log('[renderer] Stripping UTF-8 BOM');
                markdown = markdown.slice(1);
            }
            console.log(`[renderer] Loaded markdown: ${markdown.length} chars`);
            const html = this._md.parse(markdown);
            console.log(`[renderer] Parsed HTML: ${html.length} chars`);
            const sanitizedHtml = DOMPurify.sanitize(html);
            console.log(`[renderer] Sanitized HTML: ${sanitizedHtml.length} chars`);
            
            if (sanitizedHtml.length < html.length * 0.5) {
                console.warn('[renderer] Sanitization removed significant content. Check DOMPurify config.');
            }
            
            if (contentEl) {
                console.log('[renderer] Content element found, proceeding with insertion...');
                
                // Wrap content in a container for Paged.js stability
                const wrappedContent = `<div class="markdown-body">${sanitizedHtml}</div>`;
                console.log('[renderer] Wrapped content prepared:', wrappedContent.length, 'chars');
                
                // Clear any existing content first
                contentEl.innerHTML = '';
                console.log('[renderer] Content element cleared');
                
                // Insert the new content
                contentEl.innerHTML = wrappedContent;
                console.log('[renderer] Content inserted via innerHTML');
                
                // Immediate verification
                const immediateLength = contentEl.innerHTML.length;
                const immediateText = contentEl.textContent.trim();
                const hasMarkdownBody = !!contentEl.querySelector('.markdown-body');
                
                console.log('[renderer] Immediate verification:', {
                    htmlLength: immediateLength,
                    textLength: immediateText.length,
                    hasWrapper: hasMarkdownBody,
                    preview: immediateText.substring(0, 50)
                });
                
                // Wait a moment and check again
                setTimeout(() => {
                    const delayedLength = contentEl.innerHTML.length;
                    const delayedText = contentEl.textContent.trim();
                    const stillHasWrapper = !!contentEl.querySelector('.markdown-body');
                    
                    console.log('[renderer] Delayed verification (100ms):', {
                        htmlLength: delayedLength,
                        textLength: delayedText.length,
                        hasWrapper: stillHasWrapper,
                        changed: delayedLength !== immediateLength
                    });
                }, 100);
                
                if (immediateText.length > 100) {
                    console.log('[renderer] Content successfully rendered');
                    return true; // Success!
                } else {
                    console.warn('[renderer] Content appears empty after render');
                    contentEl.innerHTML = `
                        <div class="warning-box">
                            <h2>No content rendered</h2>
                            <p>The markdown was loaded (${markdown.length} chars) but produced no visible content. Possible causes:</p>
                            <ul>
                                <li>Markdown contains only headings hidden by print pagination before Paged.js finishes</li>
                                <li>Sanitization removed all content</li>
                                <li>Styles are hiding the content</li>
                            </ul>
                            <p>Try adding ?nopaged to the URL to bypass pagination, or check the browser console for errors.</p>
                        </div>`;
                    return false;
                }
            } else {
                console.error('[renderer] Content element not found!');
            }
            return false;
        } catch (error) {
            console.warn('Could not load specification markdown:', error);
            // Fallback: show instructions to copy the file
            this.showCopyInstructions();
            return false;
        }
    }

    showCopyInstructions() {
        const el = document.getElementById('content');
        if (!el) return;
        el.innerHTML = `
            <div class="info-box" style="margin: 2rem 0; text-align: center;">
                <h2>Setup Required</h2>
                <p>To render the documentation, please copy your <code>PROJECT_SPECIFICATION.md</code> file to the <code>docs</code> directory, or run a local server from the project root.</p>
                <p>Alternatively, run: <code>npm run dev</code> from the docs directory.</p>
            </div>
        `;
    }

    showError(error) {
        const el = document.getElementById('content');
        if (!el) return;
        el.innerHTML = `
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
        const tocContainer = document.getElementById('toc');
        
        if (!content || !tocContainer) {
            console.warn('[renderer] Content or TOC container not found, skipping TOC generation');
            return;
        }
        
        const headings = content.querySelectorAll('h1, h2, h3');
        
        if (headings.length === 0) {
            console.warn('[renderer] No headings found for TOC');
            tocContainer.innerHTML = '<div class="toc-entry">No sections found</div>';
            return;
        }
        
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
        
        if (!content) {
            console.warn('[renderer] Content element not found, skipping enhancements');
            return;
        }
        
        // Enhance code blocks
        this.enhanceCodeBlocks(content);

        // Trigger Prism highlighting for inserted content
        if (window.Prism && Prism.highlightAllUnder) {
            try { Prism.highlightAllUnder(content); } catch (e) { console.warn('Prism highlight failed', e); }
        }
        
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
            // Do NOT keep-with-next on h1 to avoid large unbreakable blocks
        });

        const h2Elements = content.querySelectorAll('h2');
        h2Elements.forEach(h2 => {
            // No keep-with-next to let pagination split as needed
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

        // Initialize Mermaid if available
        if (window.mermaid) {
            try {
                const darkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                mermaid.initialize({ startOnLoad: false, theme: darkMode ? 'dark' : 'default' });
                mermaid.init(undefined, content.querySelectorAll('.mermaid'));
            } catch (e) {
                console.warn('Mermaid render failed', e);
            }
        }
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

    async setupPagedJS() {
        // Option to skip Paged.js for debugging
        const params = new URLSearchParams(window.location.search);
        if (params.has('nopaged')) {
            console.warn('[renderer] Paged.js disabled via ?nopaged');
            return;
        }

        if (typeof Paged === 'undefined' || !Paged) {
            console.log('[renderer] Paged.js not loaded; loading dynamically...');
            try {
                await this.loadScript('node_modules/pagedjs/dist/paged.polyfill.js');
                console.log('[renderer] Paged.js loaded');
            } catch (e) {
                console.warn('[renderer] Failed to load Paged.js dynamically:', e);
                return;
            }
        }

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

        // Register the handler safely
        try {
            Paged.registerHandlers(MyHandler);
        } catch (e) {
            console.error('[renderer] Failed to register Paged.js handler:', e);
            // Show non-paged content and hint
            const el = document.getElementById('content');
            if (el) {
                const hint = document.createElement('div');
                hint.className = 'warning-box';
                hint.innerHTML = '<strong>Pagination disabled:</strong> The print engine encountered an error and was disabled. You can still read the content, or add ?nopaged to the URL to suppress this notice.';
                el.prepend(hint);
            }
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = src;
            s.onload = () => resolve();
            s.onerror = (e) => reject(e);
            document.head.appendChild(s);
        });
    }
}

// Initialize when DOM is ready
async function initializeRenderer() {
    console.log('[app] Initializing renderer...');
    
    // Wait for DOM to be completely ready
    if (document.readyState !== 'complete') {
        console.log('[app] Waiting for document to be complete...');
        await new Promise(resolve => {
            if (document.readyState === 'complete') {
                resolve();
            } else {
                window.addEventListener('load', resolve);
            }
        });
    }
    
    // Double-check that required elements exist
    const contentEl = document.getElementById('content');
    const tocEl = document.getElementById('toc');
    
    console.log('[app] DOM readiness check:', {
        readyState: document.readyState,
        contentExists: !!contentEl,
        tocExists: !!tocEl
    });
    
    if (!contentEl) {
        console.error('[app] Content element not found! Cannot initialize renderer.');
        return;
    }
    
    const renderer = new DocumentRenderer();
    await renderer.init();
}

// Try multiple initialization strategies
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeRenderer);
} else {
    // DOM is already ready
    initializeRenderer();
}

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
