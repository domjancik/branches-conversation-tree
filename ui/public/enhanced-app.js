class EnhancedConversationTreeApp {
    constructor() {
        this.data = null;
        this.config = null;
        this.selectedNode = null;
        this.svg = null;
        this.g = null;
        this.linksContainer = null;
        this.linkImagesContainer = null;
        this.nodesContainer = null;
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
        this.nodeImages = new Map();
        this.nodeImagesList = new Map(); // cache of all images per node (for branch rendering)
        this.audioContext = null;
        this.audioBuffers = new Map();
        this.isPlaying = false;
        this.currentAudioSource = null;
        this.zoomBehavior = null;
        
        // Enhanced visualization features
        this.enableWaveformVisualization = true;
        this.enableAmplitudeBasedBranches = true;
        this.enableSpiralLayout = false;
        this.enableParticleEffects = false;
        this.enableVolumetricLayers = false;
        
        // Animation and timing
        this.animationFrameId = null;
        this.particleSystem = null;

        // Link image placement parameters (editable via UI)
        this.linkImageParams = {
            startOffset: 0.3, // fraction from parent toward child (0-1)
            endOffset: 0.7,   // fraction from parent toward child (0-1)
            imageSize: 28,    // px
            borderRadius: 6,  // px (uses CSS clip-path rounding)
            spacing: 0,       // reserved for future advanced spacing
            maxPerLink: 8     // cap
        };
        this.presetsKey = 'linkImageParamsPresets';
        
        this.init();
    }

    async init() {
        this.setupAudioContext();
        this.setupEventListeners();
        await this.loadConfig();
        await this.loadData();
        this.populateRootSelector();
        this.initializeVisualization();
        this.render();
        this.setupEnhancedControls();
        this.setupParamsPanel();
    }

    setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            this.frequencyData = new Uint8Array(this.analyser.frequencyBinCount);
            this.timeDomainData = new Uint8Array(this.analyser.fftSize);
        } catch (error) {
            console.warn('Web Audio API not supported:', error);
        }
    }

setupEventListeners() {
        // Existing event listeners
        document.getElementById('resetZoom').addEventListener('click', () => this.resetZoom());
        document.getElementById('expandAll').addEventListener('click', () => this.expandAll());
        document.getElementById('collapseAll').addEventListener('click', () => this.collapseAll());
        document.getElementById('layoutToggle').addEventListener('click', () => this.toggleLayout());
        document.getElementById('rootSelector').addEventListener('change', (e) => this.switchRoot(e.target.value));
        
        // Camera controls (if present)
        const zoomInBtn = document.getElementById('zoomIn');
        const zoomOutBtn = document.getElementById('zoomOut');
        const panLeftBtn = document.getElementById('panLeft');
        const panRightBtn = document.getElementById('panRight');
        const panUpBtn = document.getElementById('panUp');
        const panDownBtn = document.getElementById('panDown');
        if (zoomInBtn) zoomInBtn.addEventListener('click', () => this.zoomIn());
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => this.zoomOut());
        if (panLeftBtn) panLeftBtn.addEventListener('click', () => this.pan(-100, 0));
        if (panRightBtn) panRightBtn.addEventListener('click', () => this.pan(100, 0));
        if (panUpBtn) panUpBtn.addEventListener('click', () => this.pan(0, -100));
        if (panDownBtn) panDownBtn.addEventListener('click', () => this.pan(0, 100));
        
        window.addEventListener('resize', () => this.handleResize());
        
        // Audio element event listeners
        const audioPlayer = document.getElementById('audio-player');
        if (audioPlayer) {
            audioPlayer.addEventListener('play', () => this.onAudioPlay());
            audioPlayer.addEventListener('pause', () => this.onAudioPause());
            audioPlayer.addEventListener('ended', () => this.onAudioEnd());
            audioPlayer.addEventListener('timeupdate', () => this.onAudioTimeUpdate());
        }
    }

    setupEnhancedControls() {
        const controlsContainer = document.querySelector('.controls');
        
        // Enhanced visualization controls
        const enhancedControls = document.createElement('div');
        enhancedControls.className = 'enhanced-controls';
        enhancedControls.innerHTML = `
            <button id="toggleWaveform" class="btn">Waveform: ${this.enableWaveformVisualization ? 'ON' : 'OFF'}</button>
            <button id="toggleAmplitudeBranches" class="btn">Branch Width: ${this.enableAmplitudeBasedBranches ? 'ON' : 'OFF'}</button>
            <button id="toggleSpiralLayout" class="btn">Spiral: ${this.enableSpiralLayout ? 'ON' : 'OFF'}</button>
            <button id="toggleParticles" class="btn">Particles: ${this.enableParticleEffects ? 'ON' : 'OFF'}</button>
            <button id="toggleVolumetric" class="btn">3D Layers: ${this.enableVolumetricLayers ? 'ON' : 'OFF'}</button>
        `;
        
        controlsContainer.appendChild(enhancedControls);
        
        // Enhanced control event listeners
        document.getElementById('toggleWaveform').addEventListener('click', () => this.toggleWaveformVisualization());
        document.getElementById('toggleAmplitudeBranches').addEventListener('click', () => this.toggleAmplitudeBranches());
        document.getElementById('toggleSpiralLayout').addEventListener('click', () => this.toggleSpiralLayout());
        document.getElementById('toggleParticles').addEventListener('click', () => this.toggleParticleEffects());
        document.getElementById('toggleVolumetric').addEventListener('click', () => this.toggleVolumetricLayers());
    }

    async loadConfig() {
        try {
            const apiUrl = window.API_BASE_URL ? `${window.API_BASE_URL}/api/config` : '/api/config';
            const response = await fetch(apiUrl);
            this.config = await response.json();
            
            this.margin = this.config.treeMargin;
            this.nodeRadius = this.config.nodeRadius;
            this.duration = this.config.animationDuration;
            
            console.log('Loaded config:', this.config);
        } catch (error) {
            console.error('Error loading config:', error);
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
            const apiUrl = window.API_BASE_URL ? `${window.API_BASE_URL}/api/tree-data` : '/api/tree-data';
            const response = await fetch(apiUrl);
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
            .attr('height', '100%');

        // Setup zoom behavior and camera controls
        this.zoomBehavior = d3.zoom().on('zoom', (event) => {
            this.g.attr('transform', event.transform);
            this.currentTransform = event.transform;
        });
        this.svg.call(this.zoomBehavior)
            .on('dblclick.zoom', null);

        // Create defs for filters and effects
        const defs = this.svg.append('defs');
        this.createSVGFilters(defs);

        // Create main group
        this.g = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Setup initial tree layout
        this.setupTreeLayout();

// Structured layers for proper z-ordering
        this.particleContainer = this.g.append('g').attr('class', 'particles');
        this.linksContainer = this.g.append('g').attr('class', 'links');
        this.linkImagesContainer = this.g.append('g').attr('class', 'link-images');
        this.waveformContainer = this.g.append('g').attr('class', 'waveforms');
        this.nodesContainer = this.g.append('g').attr('class', 'nodes');

        // Create root from first tree
        if (this.data.roots && this.data.roots.length > 0) {
            this.root = d3.hierarchy(this.data.roots[0], d => d.children);
            this.root.x0 = this.width / 2;
            this.root.y0 = 0;

            // Calculate audio amplitude data for each node
            this.calculateAudioAmplitudes(this.root);

            if (this.root.children) {
                this.root.children.forEach(d => this.collapse(d));
            }
        }

        // Create tooltip
        this.tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);

        // Start animation loop for enhanced features
        this.startAnimationLoop();
    }

    createSVGFilters(defs) {
        // Glow effect
        const glow = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');

        glow.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');

        const feMerge = glow.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Motion blur for particles
        const motionBlur = defs.append('filter')
            .attr('id', 'motion-blur');
        motionBlur.append('feGaussianBlur')
            .attr('in', 'SourceGraphic')
            .attr('stdDeviation', '2,0');

        // Volumetric effect
        const volumetric = defs.append('filter')
            .attr('id', 'volumetric')
            .attr('x', '-100%')
            .attr('y', '-100%')
            .attr('width', '300%')
            .attr('height', '300%');
        
        volumetric.append('feGaussianBlur')
            .attr('stdDeviation', '8')
            .attr('result', 'blur');
        volumetric.append('feColorMatrix')
            .attr('in', 'blur')
            .attr('values', '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.6 0');
    }

    calculateAudioAmplitudes(node) {
        // Calculate amplitude based on audio duration and other factors
        const duration = node.data.duration || Math.random() * 10;
        const baseAmplitude = Math.sqrt(duration) * 0.5;
        const variation = (Math.random() - 0.5) * 0.3;
        
        node.audioAmplitude = Math.max(0.1, Math.min(1.0, baseAmplitude + variation));
        
        if (node.children) {
            node.children.forEach(child => this.calculateAudioAmplitudes(child));
        }
    }

    render() {
        if (!this.root) return;

        const treeData = this.enableSpiralLayout ? 
            this.calculateSpiralLayout(this.root) : 
            this.tree(this.root);

        const nodes = treeData.descendants();
        const links = treeData.descendants().slice(1);

        this.renderNodes(nodes);
        this.renderLinks(links);
        this.renderWaveforms(nodes);
        this.renderParticles();

        // Store the old positions for transition
        nodes.forEach(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }

    renderNodes(nodes) {
const node = (this.nodesContainer || this.g).selectAll('.node')
            .data(nodes, d => d.id || (d.id = ++this.nodeCounter));

        const nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${this.root.x0},${this.root.y0})`)
            .on('click', (event, d) => this.nodeSelect(event, d))
            .on('dblclick', (event, d) => this.nodeToggle(event, d))
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());

        // Create dynamic circle size based on audio amplitude
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

        // Add transcription text
        nodeEnter.append('text')
            .attr('class', 'node-transcription')
            .attr('dy', this.layoutMode === 'horizontal' ? '1.2em' : '2.5em')
            .attr('x', this.layoutMode === 'horizontal' ? 15 : 0)
            .attr('text-anchor', this.layoutMode === 'horizontal' ? 'start' : 'middle')
            .text(d => d.data.transcriptionPreview || '')
            .style('fill-opacity', 1e-6)
            .style('font-size', '10px')
            .style('fill', '#666');

        // Add thumbnail images
        nodeEnter.append('image')
            .attr('class', 'node-thumbnail')
            .attr('width', 24)
            .attr('height', 24)
            .attr('x', this.layoutMode === 'horizontal' ? -36 : -12)
            .attr('y', this.layoutMode === 'horizontal' ? -12 : -36)
            .style('opacity', 0);

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

        // Update circle with amplitude-based sizing
        nodeUpdate.select('circle')
            .transition()
            .duration(this.duration)
            .attr('r', d => {
                let baseRadius = this.nodeRadius;
                if (this.enableAmplitudeBasedBranches && d.audioAmplitude) {
                    baseRadius = this.nodeRadius * (0.5 + d.audioAmplitude * 1.5);
                }
                return baseRadius;
            })
            .style('fill', d => d._children ? '#e74c3c' : '#fff')
            .attr('class', d => d === this.selectedNode ? 'selected' : '')
            .style('filter', d => {
                if (this.enableVolumetricLayers && d.audioAmplitude > 0.7) {
                    return 'url(#glow)';
                }
                return null;
            });

        // Update text positions
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

        nodeUpdate.select('.node-thumbnail')
            .attr('x', this.layoutMode === 'horizontal' ? -36 : -12)
            .attr('y', this.layoutMode === 'horizontal' ? -12 : -36);

        // Load and display thumbnail images
nodeUpdate.each(async (d, i, nodes) => {
            const nodeElement = d3.select(nodes[i]);
            const imageElement = nodeElement.select('.node-thumbnail');
            
            const imageData = await this.loadNodeImage(d.data);
            
            if (imageData && imageData.image_file_path) {
                const imgBase = window.API_BASE_URL ? `${window.API_BASE_URL}` : '';
                const imageUrl = `${imgBase}/images/${encodeURIComponent(imageData.image_file_path)}`;
                imageElement
                    .attr('xlink:href', imageUrl)
                    .style('opacity', 1)
                    .on('error', function() {
                        d3.select(this).style('opacity', 0);
                    });
            } else {
                imageElement.style('opacity', 0);
            }
        });

        const nodeExit = node.exit().transition()
            .duration(this.duration)
            .attr('transform', d => `translate(${this.root.x},${this.root.y})`)
            .remove();

        nodeExit.select('circle').attr('r', 1e-6);
        nodeExit.select('text').style('fill-opacity', 1e-6);
    }

    renderLinks(links) {
const link = (this.linksContainer || this.g).selectAll('.link')
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
            .attr('d', d => this.diagonal(d, d.parent))
            .style('stroke-width', d => {
                if (this.enableAmplitudeBasedBranches && d.audioAmplitude) {
                    // Use audio amplitude to determine branch thickness
                    return Math.max(1, d.audioAmplitude * 8) + 'px';
                }
                return '2px';
            })
            .style('opacity', d => {
                if (this.enableVolumetricLayers) {
                    return 0.6 + (d.audioAmplitude || 0) * 0.4;
                }
                return 1;
            });

        // Render images along each link for the child node
        this.renderLinkImages(links);

        const linkExit = link.exit().transition()
            .duration(this.duration)
            .attr('d', d => {
                const o = { x: this.root.x, y: this.root.y };
                return this.diagonal(o, o);
            })
            .remove();
    }

    renderWaveforms(nodes) {
        if (!this.enableWaveformVisualization) {
            this.waveformContainer.selectAll('*').remove();
            return;
        }

        const waveforms = this.waveformContainer.selectAll('.waveform')
            .data(nodes.filter(d => d.data.duration), d => d.id);

        const waveformEnter = waveforms.enter()
            .append('g')
            .attr('class', 'waveform');

        waveformEnter.each((d, i, nodes) => {
            const waveformGroup = d3.select(nodes[i]);
            this.createWaveformVisualization(waveformGroup, d);
        });

        waveforms.transition()
            .duration(this.duration)
            .attr('transform', d => {
                if (this.layoutMode === 'horizontal') {
                    return `translate(${d.y},${d.x})`;
                } else {
                    return `translate(${d.x},${d.y})`;
                }
            });

        waveforms.exit().remove();
    }

    createWaveformVisualization(container, nodeData) {
        const duration = nodeData.data.duration || 1;
        const amplitude = nodeData.audioAmplitude || 0.5;
        const samples = 50;
        
        const waveformData = [];
        for (let i = 0; i < samples; i++) {
            const x = (i / samples) * 100 - 50;
            const freq = 0.1 + Math.random() * 0.5;
            const phase = Math.random() * Math.PI * 2;
            const y = Math.sin(i * freq + phase) * amplitude * 20;
            waveformData.push({ x, y });
        }

        const line = d3.line()
            .x(d => d.x)
            .y(d => d.y)
            .curve(d3.curveBasis);

        container.append('path')
            .datum(waveformData)
            .attr('class', 'waveform-path')
            .attr('d', line)
            .style('stroke', '#7c5cff')
            .style('stroke-width', 1.5)
            .style('fill', 'none')
            .style('opacity', 0.7)
            .style('filter', 'url(#glow)');
    }

    renderParticles() {
        if (!this.enableParticleEffects) {
            this.particleContainer.selectAll('*').remove();
            return;
        }

        const particleData = this.generateParticleData();
        
        const particles = this.particleContainer.selectAll('.particle')
            .data(particleData, d => d.id);

        particles.enter()
            .append('circle')
            .attr('class', 'particle')
            .attr('r', d => d.size)
            .attr('cx', d => d.x)
            .attr('cy', d => d.y)
            .style('fill', d => d.color)
            .style('opacity', d => d.opacity)
            .style('filter', 'url(#motion-blur)');

        particles
            .attr('cx', d => d.x)
            .attr('cy', d => d.y)
            .style('opacity', d => d.opacity);

        particles.exit().remove();
    }

    generateParticleData() {
        if (!this.particleSystem) {
            this.particleSystem = [];
        }

        // Add new particles
        for (let i = 0; i < 5; i++) {
            this.particleSystem.push({
                id: Math.random(),
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: Math.random() * 3 + 1,
                color: d3.interpolateRainbow(Math.random()),
                opacity: Math.random() * 0.7 + 0.3,
                life: 1.0
            });
        }

        // Update existing particles
        this.particleSystem = this.particleSystem.filter(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.life -= 0.01;
            particle.opacity = particle.life;

            return particle.life > 0 && 
                   particle.x >= 0 && particle.x <= this.width &&
                   particle.y >= 0 && particle.y <= this.height;
        });

        return this.particleSystem.slice(-100); // Limit particles
    }

    calculateSpiralLayout(root) {
        const spiralFactor = 3.52;
        const angleIncrement = Math.PI * 2 / spiralFactor;
        
        function positionNode(node, depth = 0, angle = 0) {
            const radius = depth * 80;
            const spiralAngle = angle + depth * angleIncrement;
            
            node.x = Math.cos(spiralAngle) * radius + this.width / 2;
            node.y = Math.sin(spiralAngle) * radius + this.height / 2;
            
            if (node.children) {
                const childAngleStep = Math.PI * 2 / node.children.length;
                node.children.forEach((child, i) => {
                    positionNode.call(this, child, depth + 1, angle + i * childAngleStep);
                });
            }
        }
        
        positionNode.call(this, root);
        return root;
    }

    startAnimationLoop() {
        const animate = () => {
            if (this.enableParticleEffects) {
                this.renderParticles();
            }
            
            if (this.enableWaveformVisualization && this.isPlaying) {
                this.updateWaveformsWithAudio();
            }
            
            this.animationFrameId = requestAnimationFrame(animate);
        };
        
        animate();
    }

    updateWaveformsWithAudio() {
        if (!this.analyser) return;
        
        this.analyser.getByteFrequencyData(this.frequencyData);
        this.analyser.getByteTimeDomainData(this.timeDomainData);
        
        // Update waveform visualizations based on real audio data
        this.waveformContainer.selectAll('.waveform-path')
            .style('stroke-width', () => {
                const average = Array.from(this.frequencyData)
                    .reduce((sum, val) => sum + val, 0) / this.frequencyData.length;
                return 1 + (average / 128) * 3;
            })
            .style('opacity', () => {
                const average = Array.from(this.frequencyData)
                    .reduce((sum, val) => sum + val, 0) / this.frequencyData.length;
                return 0.4 + (average / 255) * 0.6;
            });
    }

    onAudioPlay() {
        this.isPlaying = true;
        
        if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        // Connect audio to analyser
        const audioPlayer = document.getElementById('audio-player');
        if (audioPlayer && this.audioContext) {
            try {
                const source = this.audioContext.createMediaElementSource(audioPlayer);
                source.connect(this.analyser);
                this.analyser.connect(this.audioContext.destination);
                this.currentAudioSource = source;
            } catch (error) {
                console.warn('Error connecting audio to analyser:', error);
            }
        }
    }

    onAudioPause() {
        this.isPlaying = false;
    }

    onAudioEnd() {
        this.isPlaying = false;
        if (this.currentAudioSource) {
            this.currentAudioSource.disconnect();
            this.currentAudioSource = null;
        }
    }

    onAudioTimeUpdate() {
        // Could implement time-based visual effects here
    }

    // Enhanced control toggle methods
    toggleWaveformVisualization() {
        this.enableWaveformVisualization = !this.enableWaveformVisualization;
        this.updateControlButton('toggleWaveform', 'Waveform', this.enableWaveformVisualization);
        this.render();
    }

    toggleAmplitudeBranches() {
        this.enableAmplitudeBasedBranches = !this.enableAmplitudeBasedBranches;
        this.updateControlButton('toggleAmplitudeBranches', 'Branch Width', this.enableAmplitudeBasedBranches);
        this.render();
    }

    toggleSpiralLayout() {
        this.enableSpiralLayout = !this.enableSpiralLayout;
        this.updateControlButton('toggleSpiralLayout', 'Spiral', this.enableSpiralLayout);
        this.setupTreeLayout();
        this.render();
    }

    toggleParticleEffects() {
        this.enableParticleEffects = !this.enableParticleEffects;
        this.updateControlButton('toggleParticles', 'Particles', this.enableParticleEffects);
        if (!this.enableParticleEffects) {
            this.particleContainer.selectAll('*').remove();
            this.particleSystem = null;
        }
    }

    toggleVolumetricLayers() {
        this.enableVolumetricLayers = !this.enableVolumetricLayers;
        this.updateControlButton('toggleVolumetric', '3D Layers', this.enableVolumetricLayers);
        this.render();
    }

    // Floating parameters panel for link images
    setupParamsPanel() {
        // Create toggle button if not present (in case HTML couldn't be edited)
        let toggleBtn = document.getElementById('paramsToggle');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.id = 'paramsToggle';
            toggleBtn.className = 'btn';
            toggleBtn.textContent = '⚙️ Params';
            Object.assign(toggleBtn.style, {
                position: 'fixed', right: '16px', bottom: '16px', zIndex: 2000,
                boxShadow: '0 6px 18px rgba(0,0,0,0.4)'
            });
            document.body.appendChild(toggleBtn);
        }

        let panel = document.getElementById('paramsPanel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'paramsPanel';
            Object.assign(panel.style, {
                position: 'fixed', right: '16px', bottom: '70px', width: '320px', maxHeight: '70vh',
                overflow: 'auto', zIndex: 2000, display: 'none',
                background: 'rgba(15,15,35,0.95)', border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '12px', padding: '14px', backdropFilter: 'blur(10px)'
            });
            panel.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="color:#7c5cff;">Link Image Parameters</strong>
                    <button id="paramsClose" class="btn" style="padding:4px 10px;">✖</button>
                </div>
                <div style="display:grid; grid-template-columns: 1fr auto; gap:8px; align-items:center;">
                    <label>Start offset (0-1)</label>
                    <input id="paramStartOffset" type="number" step="0.05" min="0" max="1" style="width:90px;">
                    <label>End offset (0-1)</label>
                    <input id="paramEndOffset" type="number" step="0.05" min="0" max="1" style="width:90px;">
                    <label>Image size (px)</label>
                    <input id="paramImageSize" type="number" min="8" max="128" step="2" style="width:90px;">
                    <label>Border radius (px)</label>
                    <input id="paramBorderRadius" type="number" min="0" max="32" step="1" style="width:90px;">
                    <label>Max per link</label>
                    <input id="paramMaxPerLink" type="number" min="1" max="20" step="1" style="width:90px;">
                </div>
                <hr style="border:none; border-top:1px solid rgba(255,255,255,0.1); margin:10px 0;"/>
                <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                    <input id="presetName" type="text" placeholder="Preset name" style="flex:1; min-width:120px; padding:6px 8px; border-radius:8px; border:1px solid rgba(255,255,255,0.15); background:rgba(255,255,255,0.08); color:#fff;">
                    <button id="savePreset" class="btn">Save</button>
                    <select id="presetSelect" class="root-selector" style="min-width:140px;"></select>
                    <button id="loadPreset" class="btn">Load</button>
                    <button id="deletePreset" class="btn" style="background:linear-gradient(135deg, rgba(255,99,99,0.8), rgba(196, 113, 113, 0.8)); border-color: rgba(255,99,99,0.5);">Delete</button>
                </div>
            `;
            document.body.appendChild(panel);
        }

        const applyInputs = () => {
            document.getElementById('paramStartOffset').value = this.linkImageParams.startOffset;
            document.getElementById('paramEndOffset').value = this.linkImageParams.endOffset;
            document.getElementById('paramImageSize').value = this.linkImageParams.imageSize;
            document.getElementById('paramBorderRadius').value = this.linkImageParams.borderRadius;
            document.getElementById('paramMaxPerLink').value = this.linkImageParams.maxPerLink;
        };
        applyInputs();

        const show = () => panel.style.display = 'block';
        const hide = () => panel.style.display = 'none';
        toggleBtn.onclick = () => panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        document.getElementById('paramsClose').onclick = hide;

        const onInputChange = () => {
            const start = parseFloat(document.getElementById('paramStartOffset').value);
            const end = parseFloat(document.getElementById('paramEndOffset').value);
            const size = parseInt(document.getElementById('paramImageSize').value, 10);
            const radius = parseInt(document.getElementById('paramBorderRadius').value, 10);
            const maxPerLink = parseInt(document.getElementById('paramMaxPerLink').value, 10);
            // Ensure valid bounds
            this.linkImageParams.startOffset = Math.max(0, Math.min(1, start));
            this.linkImageParams.endOffset = Math.max(0, Math.min(1, end));
            if (this.linkImageParams.endOffset < this.linkImageParams.startOffset) {
                this.linkImageParams.endOffset = this.linkImageParams.startOffset;
            }
            this.linkImageParams.imageSize = Math.max(8, Math.min(128, size));
            this.linkImageParams.borderRadius = Math.max(0, Math.min(32, radius));
            this.linkImageParams.maxPerLink = Math.max(1, Math.min(20, maxPerLink));
            this.render();
        };

        ['paramStartOffset', 'paramEndOffset', 'paramImageSize', 'paramBorderRadius', 'paramMaxPerLink']
            .forEach(id => document.getElementById(id).addEventListener('input', onInputChange));

        // Presets
        const loadPresets = () => {
            try {
                return JSON.parse(localStorage.getItem(this.presetsKey) || '{}');
            } catch { return {}; }
        };
        const savePresets = (obj) => localStorage.setItem(this.presetsKey, JSON.stringify(obj));
        const refreshPresetSelect = () => {
            const sel = document.getElementById('presetSelect');
            sel.innerHTML = '';
            const presets = loadPresets();
            Object.keys(presets).forEach(name => {
                const opt = document.createElement('option');
                opt.value = name; opt.textContent = name; sel.appendChild(opt);
            });
        };
        refreshPresetSelect();

        document.getElementById('savePreset').onclick = () => {
            const name = document.getElementById('presetName').value.trim();
            if (!name) return;
            const presets = loadPresets();
            presets[name] = {...this.linkImageParams};
            savePresets(presets);
            refreshPresetSelect();
        };
        document.getElementById('loadPreset').onclick = () => {
            const name = document.getElementById('presetSelect').value;
            const presets = loadPresets();
            if (name && presets[name]) {
                this.linkImageParams = {...presets[name]};
                applyInputs();
                this.render();
            }
        };
        document.getElementById('deletePreset').onclick = () => {
            const name = document.getElementById('presetSelect').value;
            const presets = loadPresets();
            if (name && presets[name]) {
                delete presets[name];
                savePresets(presets);
                refreshPresetSelect();
            }
        };
    }

    updateControlButton(buttonId, label, state) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.textContent = `${label}: ${state ? 'ON' : 'OFF'}`;
        }
    }

    // Existing methods adapted for enhanced features
    nodeSelect(event, d) {
        if (this.clickTimeout) {
            clearTimeout(this.clickTimeout);
            this.clickTimeout = null;
        }
        this.clickTimeout = setTimeout(() => {
            this.selectedNode = d;
            this.render();
            this.updateNodeDetails(d.data);
            this.loadAudio(d.data);
            this.loadImages(d.data.id);
            this.clickTimeout = null;
        }, 250);
    }

    nodeToggle(event, d) {
        if (this.clickTimeout) {
            clearTimeout(this.clickTimeout);
            this.clickTimeout = null;
        }

        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        this.render();
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
                <span class="detail-label">Audio Amplitude:</span>
                <span class="detail-value">${(this.selectedNode?.audioAmplitude || 0).toFixed(3)}</span>
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
            audioPlayer.style.display = 'block';
            audioPlaceholder.style.display = 'none';
            
            const audioBase = window.API_BASE_URL ? `${window.API_BASE_URL}` : '';
            const audioUrl = `${audioBase}/audio/${encodeURIComponent(nodeData.fullPath)}`;
            const sources = audioPlayer.getElementsByTagName('source');
        
            for (let source of sources) {
                source.src = audioUrl;
            }
            
            audioPlayer.load();
            
            audioPlayer.onerror = () => {
                console.error('Error loading audio:', nodeData.fullPath);
                audioPlayer.style.display = 'none';
                audioPlaceholder.style.display = 'block';
                audioPlaceholder.textContent = 'Audio file not found or unsupported format';
            };
            
            audioPlayer.onloadeddata = () => {
                console.log('Audio loaded successfully:', nodeData.fullPath);
            };
        } else {
            audioPlayer.style.display = 'none';
            audioPlaceholder.style.display = 'block';
            audioPlaceholder.textContent = 'No audio file available';
        }
    }

async loadImages(recordingId) {
        try {
            const apiUrl = window.API_BASE_URL ? `${window.API_BASE_URL}/api/recordings/${recordingId}/images` : `/api/recordings/${recordingId}/images`;
            const response = await fetch(apiUrl);
            const images = await response.json();
            this.displayImages(images);
        } catch (error) {
            console.error('Error loading images:', error);
            this.displayImages([]);
        }
    }

async loadNodeImage(nodeData) {
        if (this.nodeImages.has(nodeData.id)) {
            return this.nodeImages.get(nodeData.id);
        }

        try {
            const apiUrl = window.API_BASE_URL ? `${window.API_BASE_URL}/api/recordings/${nodeData.id}/images` : `/api/recordings/${nodeData.id}/images`;
            const response = await fetch(apiUrl);
            const images = await response.json();
            
            const imageData = images.length > 0 ? images[0] : null;
            this.nodeImages.set(nodeData.id, imageData);
            
            return imageData;
        } catch (error) {
            console.error('Error loading node image:', error);
            this.nodeImages.set(nodeData.id, null);
            return null;
        }
    }

displayImages(images) {
        const container = document.getElementById('images-container');
        
        if (images.length === 0) {
            container.innerHTML = '<p style="color: #777; font-style: italic;">No images available for this recording.</p>';
            return;
        }

        const imgBase = window.API_BASE_URL ? `${window.API_BASE_URL}` : '';
        container.innerHTML = images.map(image => `
            <div class="image-item">
                <img src="${imgBase}/images/${encodeURIComponent(image.image_file_path)}" 
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
            ${d.data.transcriptionPreview || 'No transcription'}<br/>
            <em>Audio Amplitude: ${(d.audioAmplitude || 0).toFixed(3)}</em>
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
        const durationSpacing = this.calculateDurationBasedSpacing(s);
        const midY = s.y + durationSpacing;
        
        return `M ${s.y} ${s.x}
                L ${midY} ${s.x}
                L ${midY} ${d.x}
                L ${d.y} ${d.x}`;
    }

    verticalDiagonal(s, d) {
        return `M ${s.x} ${s.y}
                C ${s.x} ${(s.y + d.y) / 2},
                  ${d.x} ${(s.y + d.y) / 2},
                  ${d.x} ${d.y}`;
    }

    // Render images along the connection line for each child node's images
    async renderLinkImages(links) {
        if (!this.linkImagesContainer) return;

        // Ensure images are fetched for child nodes visible in links
        const fetchPromises = links.map(async (l) => {
            const nodeId = l.data?.id;
            if (!this.nodeImagesList.has(nodeId)) {
                try {
                    const apiUrl = window.API_BASE_URL ? `${window.API_BASE_URL}/api/recordings/${nodeId}/images` : `/api/recordings/${nodeId}/images`;
                    const resp = await fetch(apiUrl);
                    const imgs = await resp.json();
                    this.nodeImagesList.set(nodeId, imgs || []);
                } catch (e) {
                    console.warn('Failed fetching images for node', nodeId, e);
                    this.nodeImagesList.set(nodeId, []);
                }
            }
        });
        await Promise.all(fetchPromises);

        // Flatten data: one entry per image with its link reference and index
        const flattened = [];
        links.forEach((l) =e {
            const nodeId = l.data?.id;
            const imgsAll = this.nodeImagesList.get(nodeId) || [];
            const imgs = imgsAll.slice(0, this.linkImageParams.maxPerLink);
            imgs.forEach((img, idx) =e {
                flattened.push({ link: l, image: img, idx, count: imgs.length });
            });
        });
        // Also include virtual root link so first node can display images
        if (this.root) {
            const rootId = this.root.data?.id;
            if (!this.nodeImagesList.has(rootId)) {
                try {
                    const apiUrl = window.API_BASE_URL ? `${window.API_BASE_URL}/api/recordings/${rootId}/images` : `/api/recordings/${rootId}/images`;
                    const resp = await fetch(apiUrl);
                    const imgs = await resp.json();
                    this.nodeImagesList.set(rootId, imgs || []);
                } catch (e) {
                    this.nodeImagesList.set(rootId, []);
                }
            }
            const rImgsAll = this.nodeImagesList.get(rootId) || [];
            const rImgs = rImgsAll.slice(0, this.linkImageParams.maxPerLink);
            const virtualParent = { x: this.root.x, y: this.root.y };
            if (this.layoutMode === 'horizontal') virtualParent.y = (this.root.y || 0) - 80; else virtualParent.y = (this.root.y || 0) - 80;
            const virtualLink = { parent: virtualParent, x: this.root.x, y: this.root.y, id: `virtual-root-${rootId}`, data: { id: rootId } };
            rImgs.forEach((img, idx) => {
                flattened.push({ link: virtualLink, image: img, idx, count: rImgs.length, virtual: true });
            });
        }

        const selection = this.linkImagesContainer.selectAll('.link-image')
            .data(flattened, d => `${d.image?.id || d.image?.image_file_path || Math.random()}-${d.link.id}`);

        const enter = selection.enter().append('image')
            .attr('class', 'link-image')
            .attr('width', 28)
            .attr('height', 28)
            .style('opacity', 0)
            .style('pointer-events', 'auto')
            .on('error', function(){ d3.select(this).style('display','none'); })
            .append('title');

        // Ensure title tooltip content
        selection.select('title').text(d => d.image?.prompt || '');

        // Update positions and hrefs
        const imgBase = window.API_BASE_URL ? `${window.API_BASE_URL}` : '';
        const size = this.linkImageParams.imageSize;
        const br = this.linkImageParams.borderRadius;

        // Ensure any new elements created on enter are selected properly
        const merged = selection.enter()
            .append('image')
            .attr('class', 'link-image')
            .merge(selection);

        merged
            .attr('width', size)
            .attr('height', size)
            .style('clip-path', `inset(0 round ${br}px)`)
            .attr('xlink:href', d => `${imgBase}/images/${encodeURIComponent(d.image.image_file_path)}`)
            .attr('transform', d => {
                const s = d.link.parent; // source (parent)
                const t = d.link; // target (child)
                // Position images spaced along the line between s and t
                const n = Math.max(1, d.count);
                const i = Math.min(d.idx, n - 1);
                const start = this.linkImageParams.startOffset;
                const end = this.linkImageParams.endOffset;
                const range = Math.max(0, end - start);
                const tPos = (n === 1) ? (start + range/2) : (start + (range * (i / (n - 1))));
                const interp = (a,b)=> a + (b-a)*tPos;
                let px, py;
                if (this.layoutMode === 'horizontal') {
                    px = interp(s.y, t.y);
                    py = interp(s.x, t.x);
                } else {
                    px = interp(s.x, t.x);
                    py = interp(s.y, t.y);
                }
                // Center the image based on configured size
                return `translate(${px - size/2},${py - size/2})`;
            })
            .transition().duration(this.duration)
            .style('opacity', 1);

        selection.exit().remove();
    }

    calculateDurationBasedSpacing(node) {
        const BASE_SPACING = 50;
        const DURATION_MULTIPLIER = 10;
        
        if (!node.data.duration) return BASE_SPACING;
        
        const amplitudeMultiplier = this.enableAmplitudeBasedBranches ? 
            (node.audioAmplitude || 1) : 1;
        
        return BASE_SPACING + (node.data.duration * DURATION_MULTIPLIER * amplitudeMultiplier);
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
        if (!this.zoomBehavior) return;
        this.svg.transition().duration(750).call(
            this.zoomBehavior.transform,
            d3.zoomIdentity.translate(this.margin.left, this.margin.top)
        );
    }

    zoomIn() {
        if (!this.zoomBehavior) return;
        this.svg.transition().duration(250).call(this.zoomBehavior.scaleBy, 1.2);
    }

    zoomOut() {
        if (!this.zoomBehavior) return;
        this.svg.transition().duration(250).call(this.zoomBehavior.scaleBy, 1/1.2);
    }

    pan(dx, dy) {
        if (!this.zoomBehavior) return;
        this.svg.transition().duration(250).call(this.zoomBehavior.translateBy, dx, dy);
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
        
        while (selector.children.length > 1) {
            selector.removeChild(selector.lastChild);
        }
        
        if (this.data && this.data.roots) {
            this.data.roots.forEach((root, index) => {
                const option = document.createElement('option');
                option.value = index;
                
                let displayText = root.name;
                if (root.transcriptionPreview) {
                    displayText = `${root.name}: ${root.transcriptionPreview}`;
                } else if (root.transcription) {
                    const trimmed = this.truncateText(root.transcription, 50);
                    displayText = `${root.name}: ${trimmed}`;
                }
                
                option.textContent = displayText;
                if (index === 0) {
                    option.selected = true;
                }
                selector.appendChild(option);
            });
        }
    }

    toggleLayout() {
        this.layoutMode = this.layoutMode === 'vertical' ? 'horizontal' : 'vertical';
        
        const button = document.getElementById('layoutToggle');
        button.textContent = this.layoutMode === 'vertical' ? 'Horizontal Layout' : 'Vertical Layout';
        
        this.setupTreeLayout();
        this.render();
    }

    setupTreeLayout() {
        if (this.enableSpiralLayout) {
            // Spiral layout doesn't use D3's tree layout
            return;
        }
        
        if (this.layoutMode === 'horizontal') {
            this.tree = d3.tree().size([this.height, this.width]);
            if (this.root) {
                this.root.x0 = this.height / 2;
                this.root.y0 = 0;
            }
        } else {
            this.tree = d3.tree().size([this.width, this.height]);
            if (this.root) {
                this.root.x0 = this.width / 2;
                this.root.y0 = 0;
            }
        }
    }

switchRoot(rootIndex) {
        if (rootIndex === '') return;
        
        const index = parseInt(rootIndex);
        if (index >= 0 && index < this.data.roots.length) {
            this.currentRootIndex = index;
            
            this.g.selectAll('*').remove();
            
            // Recreate containers with proper order
            this.particleContainer = this.g.append('g').attr('class', 'particles');
            this.linksContainer = this.g.append('g').attr('class', 'links');
            this.linkImagesContainer = this.g.append('g').attr('class', 'link-images');
            this.waveformContainer = this.g.append('g').attr('class', 'waveforms');
            this.nodesContainer = this.g.append('g').attr('class', 'nodes');
            
            this.root = d3.hierarchy(this.data.roots[index], d => d.children);
            this.root.x0 = this.width / 2;
            this.root.y0 = 0;
            
            this.calculateAudioAmplitudes(this.root);
            
            if (this.root.children) {
                this.root.children.forEach(d => this.collapse(d));
            }
            
            this.selectedNode = null;
            document.getElementById('node-details').innerHTML = '<h3>Select a node to view details</h3>';
            document.getElementById('images-container').innerHTML = '';
            
            const audioPlayer = document.getElementById('audio-player');
            const audioPlaceholder = document.getElementById('audio-placeholder');
            audioPlayer.style.display = 'none';
            audioPlaceholder.style.display = 'block';
            audioPlaceholder.textContent = 'No audio selected';
            
            this.render();
            this.resetZoom();
        }
    }

    destroy() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}

// Initialize the enhanced application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.app = new EnhancedConversationTreeApp();
        console.log('Enhanced Conversation Tree App initialized successfully');
    } catch (error) {
        console.error('Error initializing Enhanced Conversation Tree App:', error);
        // Fallback - would need original app.js loaded for this to work
        if (typeof ConversationTreeApp !== 'undefined') {
            window.app = new ConversationTreeApp();
            console.log('Fallback to original app');
        }
    }
});
