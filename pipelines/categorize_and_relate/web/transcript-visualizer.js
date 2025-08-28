/**
 * Transcript Visualizer Component
 * 
 * Displays transcript text with visual highlights for categorized segments.
 * Uses precise character-based positioning from pipeline output to avoid AI counting issues.
 */

class TranscriptVisualizer {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            showCategories: true,
            showConnections: true,
            showOpenTopics: true,
            highlightOnHover: true,
            colorScheme: 'pastel',
            ...options
        };
        
        this.transcript = '';
        this.segments = [];
        this.connections = [];
        this.openTopics = [];
        this.topicColorMap = new Map();
        
        this.init();
    }
    
    init() {
        this.container.className = 'transcript-visualizer';
        this.createStyles();
        this.render();
    }
    
    createStyles() {
        if (document.getElementById('transcript-visualizer-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'transcript-visualizer-styles';
        styles.textContent = `
            .transcript-visualizer {
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .transcript-header {
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }
            
            .transcript-title {
                font-size: 1.5em;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            
            .transcript-controls {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .control-button {
                padding: 5px 12px;
                border: 1px solid #ccc;
                background: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
            }
            
            .control-button.active {
                background: #007acc;
                color: white;
                border-color: #007acc;
            }
            
            .control-button:hover {
                background: #f0f0f0;
            }
            
            .control-button.active:hover {
                background: #005a9e;
            }
            
            .transcript-content {
                position: relative;
                font-size: 1.1em;
                line-height: 1.8;
                padding: 20px;
                background: #fafafa;
                border-radius: 6px;
                margin: 20px 0;
            }
            
            .segment-highlight {
                position: relative;
                padding: 0 1px 2px;
                margin: 0 1px;
                cursor: pointer;
                transition: all 0.2s ease;
                border-bottom-width: 6px;
                border-bottom-style: solid;
                border-bottom-color: var(--topic-color, #007acc);
            }
            
            .segment-highlight:hover {
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                transform: translateY(-1px);
            }
            
            .segment-tooltip {
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.9em;
                max-width: 300px;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transform: translateY(10px);
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            
            .segment-tooltip.visible {
                opacity: 1;
                transform: translateY(0);
            }
            
            .tooltip-category {
                font-weight: bold;
                color: #ffd700;
                margin-bottom: 4px;
            }
            
            .tooltip-summary {
                margin-bottom: 6px;
            }
            
            .tooltip-confidence {
                font-size: 0.8em;
                color: #ccc;
            }
            
            .segments-legend {
                margin: 20px 0;
                padding: 15px;
                background: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
            
            .legend-title {
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            }
            
            .legend-items {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 8px;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                transition: background 0.2s ease;
            }
            
            .legend-item:hover {
                background: #f5f5f5;
            }
            
            .legend-color {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                margin-right: 8px;
                border: 1px solid rgba(0,0,0,0.1);
            }
            
            .legend-label {
                font-size: 0.9em;
                flex: 1;
            }
            
            .connections-panel {
                margin-top: 20px;
                padding: 15px;
                background: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
            
            .connection-item {
                display: flex;
                align-items: center;
                padding: 8px;
                border-radius: 4px;
                margin-bottom: 6px;
                background: #f9f9f9;
                border-left: 3px solid #007acc;
            }
            
            .connection-type {
                font-weight: bold;
                color: #007acc;
                margin-right: 8px;
                font-size: 0.8em;
                text-transform: uppercase;
            }
            
            .connection-description {
                flex: 1;
                font-size: 0.9em;
            }
            
            .open-topics-panel {
                margin-top: 20px;
                padding: 15px;
                background: #fff8e1;
                border-radius: 6px;
                border: 1px solid #ffcc02;
            }
            
            .open-topic-item {
                padding: 10px;
                background: white;
                border-radius: 4px;
                margin-bottom: 8px;
                border-left: 3px solid #ff9800;
            }
            
            .topic-question {
                font-weight: bold;
                color: #e65100;
                margin-bottom: 4px;
            }
            
            .topic-status {
                font-size: 0.8em;
                color: #666;
                text-transform: uppercase;
            }
        `;
        document.head.appendChild(styles);
    }

    // Generate or reuse a deterministic color for a given topic/category label
    getColorForTopic(label) {
        if (!label) return '#007acc';
        if (this.topicColorMap.has(label)) return this.topicColorMap.get(label);
        const hue = this.hashString(label) % 360;
        const saturation = 70; // percent
        const lightness = 50; // percent
        const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
        this.topicColorMap.set(label, color);
        return color;
    }

    buildTopicColorMap() {
        this.topicColorMap.clear();
        const seen = new Set();
        (this.segments || []).forEach(seg => {
            const label = seg.topic || seg.category;
            if (label && !seen.has(label)) {
                seen.add(label);
                // Precompute and store color for stability
                this.getColorForTopic(label);
            }
        });
    }

    // Simple string hash -> 32-bit integer
    hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0; // Convert to 32bit int
        }
        return Math.abs(hash);
    }
         loadData(pipelineResult) {
        try {
            // Handle both raw pipeline output and server response formats
            const data = pipelineResult.result || pipelineResult;
            
            this.segments = data.segments || [];
            this.connections = data.connections_summary || [];
            this.openTopics = data.open_topics || [];
            
            // Get transcript from metadata if available
            this.transcript = pipelineResult.metadata?.transcript || '';

            // Build or update topic -> color mapping
            this.buildTopicColorMap();
            
            this.render();
        } catch (error) {
            console.error('Failed to load pipeline data:', error);
            this.showError('Failed to load transcript data');
        }
    }
    
    render() {
        this.container.innerHTML = `
            <div class="transcript-header">
                <div class="transcript-title">Transcript Analysis</div>
                <div class="transcript-controls">
                    <button class="control-button ${this.options.showCategories ? 'active' : ''}" 
                            data-toggle="categories">
                        Show Categories
                    </button>
                    <button class="control-button ${this.options.showConnections ? 'active' : ''}" 
                            data-toggle="connections">
                        Show Connections
                    </button>
                    <button class="control-button ${this.options.showOpenTopics ? 'active' : ''}" 
                            data-toggle="openTopics">
                        Show Open Topics
                    </button>
                </div>
            </div>
            
            <div class="transcript-content">
                ${this.renderTranscriptWithHighlights()}
            </div>
            
            ${this.options.showCategories ? this.renderLegend() : ''}
            ${this.options.showConnections ? this.renderConnections() : ''}
            ${this.options.showOpenTopics ? this.renderOpenTopics() : ''}
            
            <div class="segment-tooltip"></div>
        `;
        
        this.attachEventListeners();
    }
    
    renderTranscriptWithHighlights() {
        if (!this.transcript) {
            return '<p style="color: #666; font-style: italic;">No transcript available</p>';
        }
        
        // Create array of all text ranges with their segment info
        const ranges = [];
        this.segments.forEach((segment, segmentIndex) => {
            if (segment.text_ranges) {
                segment.text_ranges.forEach(range => {
                    ranges.push({
                        start: range.corrected_start_char || range.start_char || 0,
                        end: range.corrected_end_char || range.end_char || 0,
                        segment: segment,
                        segmentIndex: segmentIndex,
                        relevance: range.relevance || 1.0
                    });
                });
            }
        });
        
        // Sort ranges by start position
        ranges.sort((a, b) => a.start - b.start);
        
        // Build highlighted HTML
        let html = '';
        let currentPos = 0;
        
        ranges.forEach(range => {
            // Add text before this range
            if (range.start > currentPos) {
                html += this.escapeHtml(this.transcript.slice(currentPos, range.start));
            }
            
            // Add highlighted range with thick colored underline by topic/category
            const text = this.transcript.slice(range.start, range.end);
            const topicLabel = range.segment.topic || range.segment.category || 'Topic';
            const color = this.getColorForTopic(topicLabel);
            html += `<span class=\"segment-highlight\" 
                           data-segment-id=\"${range.segment.id}\"
                           data-segment-index=\"${range.segmentIndex}\"
                           data-topic=\"${this.escapeHtml(topicLabel)}\"
                           data-relevance=\"${range.relevance}\"
                           style=\"--topic-color: ${color}; border-bottom-color: ${color};\">\n                        ${this.escapeHtml(text)}\n                     </span>`;
            
            currentPos = Math.max(currentPos, range.end);
        });
        
        // Add remaining text
        if (currentPos < this.transcript.length) {
            html += this.escapeHtml(this.transcript.slice(currentPos));
        }
        
        return html || this.escapeHtml(this.transcript);
    }
    
    renderLegend() {
        if (this.segments.length === 0) return '';
        
        // Unique topics/categories preserving order of first appearance
        const seen = new Set();
        const topics = [];
        this.segments.forEach(seg => {
            const label = seg.topic || seg.category || 'Topic';
            if (!seen.has(label)) {
                seen.add(label);
                topics.push(label);
            }
        });
        
        const legendItems = topics.map((label) => {
            const color = this.getColorForTopic(label);
            return `
            <div class="legend-item" data-topic="${this.escapeHtml(label)}">
                <div class="legend-color" style="background: ${color}; border-color: ${color};"></div>
                <div class="legend-label">
                    <strong>${label}</strong>
                </div>
            </div>`;
        }).join('');
        
        return `
            <div class="segments-legend">
                <div class="legend-title">Topics (${topics.length})</div>
                <div class="legend-items">
                    ${legendItems}
                </div>
            </div>
        `;
    }
    
    renderConnections() {
        if (this.connections.length === 0) return '';
        
        const connectionItems = this.connections.map(conn => `
            <div class="connection-item">
                <div class="connection-type">${conn.type}</div>
                <div class="connection-description">
                    ${conn.reason} 
                    <em>(${(conn.confidence * 100).toFixed(0)}% confidence)</em>
                </div>
            </div>
        `).join('');
        
        return `
            <div class="connections-panel">
                <div class="legend-title">Relationships (${this.connections.length})</div>
                ${connectionItems}
            </div>
        `;
    }
    
    renderOpenTopics() {
        if (this.openTopics.length === 0) return '';
        
        const topicItems = this.openTopics.map(topic => `
            <div class="open-topic-item">
                <div class="topic-question">${topic.question}</div>
                <div class="topic-status">Status: ${topic.status}</div>
            </div>
        `).join('');
        
        return `
            <div class="open-topics-panel">
                <div class="legend-title">Open Questions (${this.openTopics.length})</div>
                ${topicItems}
            </div>
        `;
    }
    
    attachEventListeners() {
        // Control buttons
        this.container.querySelectorAll('.control-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const toggle = e.target.dataset.toggle;
                this.options[toggle] = !this.options[toggle];
                e.target.classList.toggle('active', this.options[toggle]);
                this.render();
            });
        });
        
        // Segment highlights
        this.container.querySelectorAll('.segment-highlight').forEach(highlight => {
            highlight.addEventListener('mouseenter', (e) => {
                this.showTooltip(e, highlight);
            });
            
            highlight.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
        
        // Legend items (click to highlight all occurrences of a topic)
        this.container.querySelectorAll('.legend-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const topic = e.currentTarget.dataset.topic;
                if (topic) {
                    this.highlightTopic(topic);
                }
            });
        });
    }
    
    showTooltip(event, highlight) {
        const tooltip = this.container.querySelector('.segment-tooltip');
        const segmentIndex = parseInt(highlight.dataset.segmentIndex);
        const segment = this.segments[segmentIndex];
        
        if (!segment) return;
        
        tooltip.innerHTML = `
            <div class="tooltip-category">${segment.category}</div>
            <div class="tooltip-summary">${segment.summary}</div>
            <div class="tooltip-confidence">Confidence: ${(segment.confidence * 100).toFixed(0)}%</div>
        `;
        
        // Position tooltip
        const rect = highlight.getBoundingClientRect();
        const containerRect = this.container.getBoundingClientRect();
        
        tooltip.style.left = (rect.left - containerRect.left) + 'px';
        tooltip.style.top = (rect.bottom - containerRect.top + 5) + 'px';
        
        tooltip.classList.add('visible');
    }
    
    hideTooltip() {
        const tooltip = this.container.querySelector('.segment-tooltip');
        tooltip.classList.remove('visible');
    }
    
    highlightSegment(segmentId) {
        // Remove previous highlights
        this.container.querySelectorAll('.segment-highlight').forEach(el => {
            el.style.boxShadow = '';
            el.style.transform = '';
        });
        
        // Highlight all instances of this segment
        this.container.querySelectorAll(`[data-segment-id=\"${segmentId}\"]`).forEach(el => {
            el.style.boxShadow = '0 4px 12px rgba(0,123,255,0.3)';
            el.style.transform = 'translateY(-2px)';
            
            // Scroll into view
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    highlightTopic(topicLabel) {
        // Remove previous highlights
        this.container.querySelectorAll('.segment-highlight').forEach(el => {
            el.style.boxShadow = '';
            el.style.transform = '';
        });
        
        // Highlight all ranges with this topic
        const matches = this.container.querySelectorAll(`[data-topic=\"${this.escapeHtml(topicLabel)}\"]`);
        matches.forEach(el => {
            el.style.boxShadow = '0 4px 12px rgba(0,123,255,0.3)';
            el.style.transform = 'translateY(-2px)';
        });
        if (matches.length) {
            matches[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    showError(message) {
        this.container.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #d32f2f;">
                <h3>Error Loading Transcript</h3>
                <p>${message}</p>
            </div>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API methods
    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
        this.render();
    }
    
    getSegments() {
        return this.segments;
    }
    
    getConnections() {
        return this.connections;
    }
    
    getOpenTopics() {
        return this.openTopics;
    }
    
    exportData() {
        return {
            transcript: this.transcript,
            segments: this.segments,
            connections: this.connections,
            openTopics: this.openTopics
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TranscriptVisualizer;
}

// Also make available globally
if (typeof window !== 'undefined') {
    window.TranscriptVisualizer = TranscriptVisualizer;
}
