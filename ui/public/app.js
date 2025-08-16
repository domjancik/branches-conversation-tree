class ConversationTreeApp {
    constructor() {
        this.data = null;
        this.config = null;
        this.selectedNode = null;
        this.svg = null;
        this.g = null;
        this.tree = null;
        this.root = null;
        this.currentRootIndex = 0;
        this.width = 0;
        this.height = 0;
        this.margin = { top: 40, right: 40, bottom: 40, left: 40 };
        this.nodeRadius = 8;
        this.duration = 750;
        this.nodeCounter = 0;
        this.layoutMode = 'vertical'; // 'vertical' or 'horizontal'

        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadConfig();
        await this.loadData();
        this.populateRootSelector();
        this.initializeVisualization();
        this.render();
    }

    setupEventListeners() {
        document.getElementById('resetZoom').addEventListener('click', () => this.resetZoom());
        document.getElementById('expandAll').addEventListener('click', () => this.expandAll());
        document.getElementById('collapseAll').addEventListener('click', () => this.collapseAll());
        document.getElementById('layoutToggle').addEventListener('click', () => this.toggleLayout());
        document.getElementById('rootSelector').addEventListener('change', (e) => this.switchRoot(e.target.value));
        
        window.addEventListener('resize', () => this.handleResize());
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            this.config = await response.json();
            
            // Update instance variables with config values
            this.margin = this.config.treeMargin;
            this.nodeRadius = this.config.nodeRadius;
            this.duration = this.config.animationDuration;
            
            console.log('Loaded config:', this.config);
        } catch (error) {
            console.error('Error loading config:', error);
            // Use defaults if config fails to load
            this.config = {
                defaultRootIndex: 0,
                maxNodeTextLength: 20,
                animationDuration: 750,
                nodeRadius: 8,
                treeMargin: { top: 40, right: 40, bottom: 40, left: 40 }
            };
        }
    }

    async loadData() {
        try {
            const response = await fetch('/api/tree-data');
            this.data = await response.json();
            console.log('Loaded tree data:', this.data);
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load conversation tree data');
        }
    }

    initializeVisualization() {
        const container = document.getElementById('tree-visualization');
        this.width = container.clientWidth - this.margin.left - this.margin.right;
        this.height = container.clientHeight - this.margin.top - this.margin.bottom;

        // Create SVG
        this.svg = d3.select('#tree-visualization')
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .call(d3.zoom().on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            }))
            .on('dblclick.zoom', null);

        // Create main group
        this.g = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Setup initial tree layout
        this.setupTreeLayout();

        // Create root from first tree (assuming there's at least one root)
        if (this.data.roots && this.data.roots.length > 0) {
            this.root = d3.hierarchy(this.data.roots[0], d => d.children);
            this.root.x0 = this.width / 2;
            this.root.y0 = 0;

            // Collapse children initially
            if (this.root.children) {
                this.root.children.forEach(d => this.collapse(d));
            }
        }

        // Create tooltip
        this.tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);
    }

    render() {
        if (!this.root) return;

        const treeData = this.tree(this.root);
        const nodes = treeData.descendants();
        const links = treeData.descendants().slice(1);

        // Update nodes
        const node = this.g.selectAll('.node')
            .data(nodes, d => d.id || (d.id = ++this.nodeCounter));

        const nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${this.root.x0},${this.root.y0})`)
            .on('click', (event, d) => this.nodeClick(event, d))
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());

        nodeEnter.append('circle')
            .attr('r', 1e-6)
            .style('fill', d => d._children ? '#e74c3c' : '#fff')
            .style('cursor', 'pointer');

        // Add node title text
        nodeEnter.append('text')
            .attr('class', 'node-title')
            .attr('dy', this.layoutMode === 'horizontal' ? '0.35em' : '1.5em')
            .attr('x', this.layoutMode === 'horizontal' ? 15 : 0)
            .attr('text-anchor', this.layoutMode === 'horizontal' ? 'start' : 'middle')
            .text(d => this.truncateText(d.data.name, this.config.maxNodeTextLength))
            .style('fill-opacity', 1e-6)
            .style('font-weight', 'bold');
        
        // Add transcription text (if available)
        nodeEnter.append('text')
            .attr('class', 'node-transcription')
            .attr('dy', this.layoutMode === 'horizontal' ? '1.2em' : '2.5em')
            .attr('x', this.layoutMode === 'horizontal' ? 15 : 0)
            .attr('text-anchor', this.layoutMode === 'horizontal' ? 'start' : 'middle')
            .text(d => d.data.transcriptionPreview || '')
            .style('fill-opacity', 1e-6)
            .style('font-size', '10px')
            .style('fill', '#666');

        const nodeUpdate = nodeEnter.merge(node);

        nodeUpdate.transition()
            .duration(this.duration)
            .attr('transform', d => {
                if (this.layoutMode === 'horizontal') {
                    return `translate(${d.y},${d.x})`;
                } else {
                    return `translate(${d.x},${d.y})`;
                }
            });

        nodeUpdate.select('circle')
            .attr('r', this.nodeRadius)
            .style('fill', d => d._children ? '#e74c3c' : '#fff')
            .attr('class', d => d === this.selectedNode ? 'selected' : '');

        // Update text positions based on layout
        nodeUpdate.select('.node-title')
            .attr('dy', this.layoutMode === 'horizontal' ? '0.35em' : '1.5em')
            .attr('x', this.layoutMode === 'horizontal' ? 15 : 0)
            .attr('text-anchor', this.layoutMode === 'horizontal' ? 'start' : 'middle')
            .style('fill-opacity', 1);
            
        nodeUpdate.select('.node-transcription')
            .attr('dy', this.layoutMode === 'horizontal' ? '1.2em' : '2.5em')
            .attr('x', this.layoutMode === 'horizontal' ? 15 : 0)
            .attr('text-anchor', this.layoutMode === 'horizontal' ? 'start' : 'middle')
            .style('fill-opacity', 1);

        const nodeExit = node.exit().transition()
            .duration(this.duration)
            .attr('transform', d => `translate(${this.root.x},${this.root.y})`)
            .remove();

        nodeExit.select('circle')
            .attr('r', 1e-6);

        nodeExit.select('text')
            .style('fill-opacity', 1e-6);

        // Update links
        const link = this.g.selectAll('.link')
            .data(links, d => d.id);

        const linkEnter = link.enter().insert('path', 'g')
            .attr('class', 'link')
            .attr('d', d => {
                const o = { x: this.root.x0, y: this.root.y0 };
                return this.diagonal(o, o);
            });

        const linkUpdate = linkEnter.merge(link);

        linkUpdate.transition()
            .duration(this.duration)
            .attr('d', d => this.diagonal(d, d.parent));

        const linkExit = link.exit().transition()
            .duration(this.duration)
            .attr('d', d => {
                const o = { x: this.root.x, y: this.root.y };
                return this.diagonal(o, o);
            })
            .remove();

        // Store the old positions for transition
        nodes.forEach(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }

    nodeClick(event, d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }

        this.selectedNode = d;
        this.render();
        this.updateNodeDetails(d.data);
        this.loadAudio(d.data);
        this.loadImages(d.data.id);
    }

    async updateNodeDetails(nodeData) {
        const detailsContainer = document.getElementById('node-details');
        
        const formatDate = (dateStr) => {
            return dateStr ? new Date(dateStr).toLocaleString() : 'N/A';
        };

        const formatDuration = (duration) => {
            if (!duration) return 'N/A';
            return `${duration.toFixed(2)}s`;
        };

        detailsContainer.innerHTML = `
            <h3>${nodeData.name}</h3>
            <div class="detail-item">
                <span class="detail-label">ID:</span>
                <span class="detail-value">${nodeData.id}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Duration:</span>
                <span class="detail-value">${formatDuration(nodeData.duration)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Created:</span>
                <span class="detail-value">${formatDate(nodeData.createdDate)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Parent:</span>
                <span class="detail-value">${nodeData.parentId || 'Root'}</span>
            </div>
            ${nodeData.parentTime ? `
                <div class="detail-item">
                    <span class="detail-label">Branch Time:</span>
                    <span class="detail-value">${formatDuration(nodeData.parentTime)}</span>
                </div>
            ` : ''}
            ${nodeData.transcription ? `
                <div class="detail-item">
                    <span class="detail-label">Transcription:</span>
                    <div class="transcription-text">${nodeData.transcription}</div>
                </div>
            ` : ''}
        `;
    }

    loadAudio(nodeData) {
        const audioPlayer = document.getElementById('audio-player');
        const audioPlaceholder = document.getElementById('audio-placeholder');
        
        if (nodeData.fullPath) {
            // Show audio player and hide placeholder
            audioPlayer.style.display = 'block';
            audioPlaceholder.style.display = 'none';
            
            // Set audio source
            const audioUrl = `/audio/${encodeURIComponent(nodeData.fullPath)}`;
            const sources = audioPlayer.getElementsByTagName('source');
            
            // Update all source elements
            for (let source of sources) {
                source.src = audioUrl;
            }
            
            // Load the audio
            audioPlayer.load();
            
            // Add error handling
            audioPlayer.onerror = () => {
                console.error('Error loading audio:', nodeData.fullPath);
                audioPlayer.style.display = 'none';
                audioPlaceholder.style.display = 'block';
                audioPlaceholder.textContent = 'Audio file not found or unsupported format';
            };
            
            // Add loaded event to show success
            audioPlayer.onloadeddata = () => {
                console.log('Audio loaded successfully:', nodeData.fullPath);
            };
        } else {
            // Hide audio player and show placeholder
            audioPlayer.style.display = 'none';
            audioPlaceholder.style.display = 'block';
            audioPlaceholder.textContent = 'No audio file available';
        }
    }

    async loadImages(recordingId) {
        try {
            const response = await fetch(`/api/recordings/${recordingId}/images`);
            const images = await response.json();
            this.displayImages(images);
        } catch (error) {
            console.error('Error loading images:', error);
            this.displayImages([]);
        }
    }

    displayImages(images) {
        const container = document.getElementById('images-container');
        
        if (images.length === 0) {
            container.innerHTML = '<p style="color: #777; font-style: italic;">No images available for this recording.</p>';
            return;
        }

        container.innerHTML = images.map(image => `
            <div class="image-item">
                <img src="/images/${encodeURIComponent(image.image_file_path)}" 
                     alt="Generated image" 
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div style="display:none; padding: 2rem; background: #f0f0f0; text-align: center; border-radius: 4px;">
                    Image not found: ${image.image_file_path}
                </div>
                <div class="image-prompt">${image.prompt}</div>
                ${image.reason ? `<div class="image-reason" style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">${image.reason}</div>` : ''}
                <div class="image-meta">
                    <span>Seed: ${image.seed || 'N/A'}</span>
                    <span>${new Date(image.created_date).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    }

    showTooltip(event, d) {
        this.tooltip.transition()
            .duration(200)
            .style('opacity', .9);
        
        this.tooltip.html(`
            <strong>${d.data.name}</strong><br/>
            ${d.data.transcriptionPreview || 'No transcription'}
        `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
    }

    hideTooltip() {
        this.tooltip.transition()
            .duration(500)
            .style('opacity', 0);
    }

    diagonal(source, destination) {
        if (this.layoutMode === 'horizontal') {
            return this.horizontalDiagonal(source, destination);
        } else {
            return this.verticalDiagonal(source, destination);
        }
    }

    horizontalDiagonal(s, d) {
        // Calculate duration-based horizontal extension
        const durationSpacing = this.calculateDurationBasedSpacing(s);
        
        // Create mostly horizontal line with minimal vertical bend at connection
        const midY = s.y + durationSpacing;
        
        return `M ${s.y} ${s.x}
                L ${midY} ${s.x}
                L ${midY} ${d.x}
                L ${d.y} ${d.x}`;
    }

    verticalDiagonal(s, d) {
        // Standard curved connection for vertical layout
        return `M ${s.x} ${s.y}
                C ${s.x} ${(s.y + d.y) / 2},
                  ${d.x} ${(s.y + d.y) / 2},
                  ${d.x} ${d.y}`;
    }

    collapse(d) {
        if (d.children) {
            d._children = d.children;
            d._children.forEach(child => this.collapse(child));
            d.children = null;
        }
    }

    expand(d) {
        if (d._children) {
            d.children = d._children;
            d.children.forEach(child => this.expand(child));
            d._children = null;
        }
    }

    expandAll() {
        this.expand(this.root);
        this.render();
    }

    collapseAll() {
        if (this.root.children) {
            this.root.children.forEach(d => this.collapse(d));
        }
        this.render();
    }

    resetZoom() {
        this.svg.transition().duration(750).call(
            d3.zoom().transform,
            d3.zoomIdentity.translate(this.margin.left, this.margin.top)
        );
    }

    handleResize() {
        const container = document.getElementById('tree-visualization');
        this.width = container.clientWidth - this.margin.left - this.margin.right;
        this.height = container.clientHeight - this.margin.top - this.margin.bottom;
        
        this.tree.size([this.width, this.height]);
        this.render();
    }

    truncateText(text, length) {
        return text.length > length ? text.substring(0, length) + '...' : text;
    }

    showError(message) {
        const container = document.getElementById('tree-visualization');
        container.innerHTML = `<div class="loading">${message}</div>`;
    }

    populateRootSelector() {
        const selector = document.getElementById('rootSelector');
        
        // Clear existing options except the first one
        while (selector.children.length > 1) {
            selector.removeChild(selector.lastChild);
        }
        
        if (this.data && this.data.roots) {
            this.data.roots.forEach((root, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${root.name} (ID: ${root.id})`;
                if (index === 0) {
                    option.selected = true;
                }
                selector.appendChild(option);
            });
        }
    }

    toggleLayout() {
        this.layoutMode = this.layoutMode === 'vertical' ? 'horizontal' : 'vertical';
        
        // Update button text
        const button = document.getElementById('layoutToggle');
        button.textContent = this.layoutMode === 'vertical' ? 'Horizontal Layout' : 'Vertical Layout';
        
        // Reconfigure tree layout
        this.setupTreeLayout();
        
        // Re-render with new layout
        this.render();
    }

    setupTreeLayout() {
        if (this.layoutMode === 'horizontal') {
            // For horizontal layout: root at left, branches spread vertically
            this.tree = d3.tree().size([this.height, this.width]);
            if (this.root) {
                this.root.x0 = this.height / 2;
                this.root.y0 = 0;
            }
        } else {
            // For vertical layout: root at top, branches spread horizontally
            this.tree = d3.tree().size([this.width, this.height]);
            if (this.root) {
                this.root.x0 = this.width / 2;
                this.root.y0 = 0;
            }
        }
    }

    calculateDurationBasedSpacing(node) {
        // Base spacing units
        const BASE_SPACING = 50;
        const DURATION_MULTIPLIER = 10; // pixels per second
        
        if (!node.data.duration) return BASE_SPACING;
        
        // Scale based on audio duration
        return BASE_SPACING + (node.data.duration * DURATION_MULTIPLIER);
    }

    switchRoot(rootIndex) {
        if (rootIndex === '') return;
        
        const index = parseInt(rootIndex);
        if (index >= 0 && index < this.data.roots.length) {
            this.currentRootIndex = index;
            
            // Clear the existing visualization
            this.g.selectAll('*').remove();
            
            // Create new root hierarchy
            this.root = d3.hierarchy(this.data.roots[index], d => d.children);
            this.root.x0 = this.width / 2;
            this.root.y0 = 0;
            
            // Collapse children initially
            if (this.root.children) {
                this.root.children.forEach(d => this.collapse(d));
            }
            
            // Reset selected node and details
            this.selectedNode = null;
            document.getElementById('node-details').innerHTML = '<h3>Select a node to view details</h3>';
            document.getElementById('images-container').innerHTML = '';
            
            // Reset audio player
            const audioPlayer = document.getElementById('audio-player');
            const audioPlaceholder = document.getElementById('audio-placeholder');
            audioPlayer.style.display = 'none';
            audioPlaceholder.style.display = 'block';
            audioPlaceholder.textContent = 'No audio selected';
            
            // Re-render the tree
            this.render();
            this.resetZoom();
        }
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ConversationTreeApp();
});
