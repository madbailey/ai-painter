/**
 * AI Assistant for MS Paint
 * Implements a local AI drawing assistant using CLIP and a small language model
 */
class AIAssistant {
    constructor(canvasAPI) {
        this.canvasAPI = canvasAPI;
        this.clipModel = null;
        this.languageModel = null;
        this.isModelLoaded = false;
        this.isGenerating = false;
        this.currentPrompt = "";
        this.drawingSteps = [];
        this.currentStepIndex = 0;
        
        // Configuration
        this.config = {
            maxSteps: 50,           // Maximum number of drawing operations
            clipFeedbackInterval: 5, // Check drawing progress every N steps
            autoCorrect: true,       // Whether to auto-correct based on CLIP feedback
            modelsPath: './models/'  // Path to model files
        };
        
        // Initialize
        this.init();
    }
    
    async init() {
        updateStatus('Initializing AI Assistant...');
        
        try {
            // Set up UI elements
            this.setupUI();
            
            // Load models when requested (not immediately to save bandwidth)
            updateStatus('AI Assistant ready - click "Load AI Models" to begin');
        } catch (error) {
            console.error('Error initializing AI Assistant:', error);
            updateStatus('Error initializing AI Assistant');
        }
    }
    
    setupUI() {
        // Create AI controls section
        const sidebar = document.querySelector('.sidebar');
        
        if (!sidebar) {
            console.error('Sidebar not found');
            return;
        }
        
        // Create AI panel
        const aiPanel = document.createElement('div');
        aiPanel.className = 'ai-panel';
        aiPanel.innerHTML = `
            <h3>AI Drawing Assistant</h3>
            <div class="ai-controls">
                <button id="loadModelsBtn" class="ai-button">Load AI Models</button>
                <div class="prompt-input">
                    <input type="text" id="drawingPrompt" placeholder="Describe what to draw..." disabled>
                    <button id="generateBtn" class="ai-button" disabled>Draw It!</button>
                </div>
                <div class="ai-status">
                    <div class="status-indicator">
                        <span>Models:</span>
                        <span id="modelsStatus">Not Loaded</span>
                    </div>
                    <div class="progress-container">
                        <div id="drawingProgress" class="progress-bar"></div>
                    </div>
                </div>
            </div>
            <div class="model-feedback" id="modelFeedback"></div>
        `;
        
        // Insert before API console
        const apiConsole = sidebar.querySelector('.api-console');
        if (apiConsole) {
            sidebar.insertBefore(aiPanel, apiConsole);
        } else {
            sidebar.appendChild(aiPanel);
        }
        
        // Setup event listeners
        document.getElementById('loadModelsBtn').addEventListener('click', this.loadModels.bind(this));
        document.getElementById('generateBtn').addEventListener('click', this.generateDrawing.bind(this));
        document.getElementById('drawingPrompt').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.generateDrawing();
            }
        });
    }
    
    async loadModels() {
        if (this.isModelLoaded) return;
        
        try {
            updateStatus('Loading AI models...');
            document.getElementById('modelsStatus').textContent = 'Loading...';
            
            // Load CLIP model (TensorFlow.js format)
            await this.loadCLIPModel();
            
            // Load Language Model (ONNX format)
            await this.loadLanguageModel();
            
            // Update UI
            this.isModelLoaded = true;
            document.getElementById('modelsStatus').textContent = 'Ready';
            document.getElementById('loadModelsBtn').textContent = 'Models Loaded';
            document.getElementById('drawingPrompt').disabled = false;
            document.getElementById('generateBtn').disabled = false;
            
            updateStatus('AI Models loaded - ready to draw!');
        } catch (error) {
            console.error('Error loading models:', error);
            document.getElementById('modelsStatus').textContent = 'Error';
            updateStatus('Error loading AI models');
        }
    }
    
    async loadCLIPModel() {
        console.log('Loading CLIP model...');
        // In a real implementation, this would use TensorFlow.js to load the model
        // For demonstration purposes, we'll simulate loading
        
        return new Promise(resolve => {
            setTimeout(() => {
                this.clipModel = {
                    name: 'CLIP-Lite',
                    scoreImage: (imageData, prompt) => {
                        // In real implementation, this would compute similarity between image and text
                        // For now, return a random score between 0-1
                        return Math.random();
                    }
                };
                console.log('CLIP model loaded');
                resolve();
            }, 1500);
        });
    }
    
    async loadLanguageModel() {
        console.log('Loading Language model...');
        // In a real implementation, this would load a small LM via ONNX Runtime
        // For demonstration purposes, we'll simulate loading
        
        return new Promise(resolve => {
            setTimeout(() => {
                this.languageModel = {
                    name: 'TinyLlama',
                    generateDrawingPlan: (prompt) => {
                        // In real implementation, this would generate API calls to draw the image
                        // For now, return a set of simple drawing operations
                        return this.simulateDrawingPlan(prompt);
                    }
                };
                console.log('Language model loaded');
                resolve();
            }, 2000);
        });
    }
    
    async generateDrawing() {
        if (!this.isModelLoaded || this.isGenerating) return;
        
        const promptInput = document.getElementById('drawingPrompt');
        const prompt = promptInput.value.trim();
        
        if (!prompt) {
            updateStatus('Please enter a drawing prompt');
            return;
        }
        
        try {
            this.isGenerating = true;
            this.currentPrompt = prompt;
            this.currentStepIndex = 0;
            
            // Clear canvas
            this.canvasAPI.clear();
            
            // Update UI
            updateStatus(`Generating drawing for: "${prompt}"`);
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('drawingPrompt').disabled = true;
            document.getElementById('drawingProgress').style.width = '0%';
            document.getElementById('modelFeedback').textContent = 'Planning drawing...';
            
            // Generate drawing plan
            console.log('Generating drawing plan for:', prompt);
            this.drawingSteps = await this.languageModel.generateDrawingPlan(prompt);
            
            // Execute drawing steps
            await this.executeDrawingSteps();
            
            // Finalize
            this.isGenerating = false;
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('drawingPrompt').disabled = false;
            document.getElementById('modelFeedback').textContent = 'Drawing completed!';
            updateStatus('Drawing completed');
        } catch (error) {
            console.error('Error generating drawing:', error);
            this.isGenerating = false;
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('drawingPrompt').disabled = false;
            updateStatus('Error generating drawing');
        }
    }
    
    async executeDrawingSteps() {
        const totalSteps = this.drawingSteps.length;
        
        for (let i = 0; i < totalSteps; i++) {
            this.currentStepIndex = i;
            
            // Update progress
            const progress = Math.round((i / totalSteps) * 100);
            document.getElementById('drawingProgress').style.width = `${progress}%`;
            
            // Execute step
            const step = this.drawingSteps[i];
            await this.executeDrawingStep(step);
            
            // Wait a bit to visualize the drawing process
            await new Promise(resolve => setTimeout(resolve, 50));
            
            // Check with CLIP for feedback every N steps
            if (this.config.autoCorrect && i % this.config.clipFeedbackInterval === 0 && i > 0) {
                await this.getFeedbackAndAdjust();
            }
        }
        
        // Final evaluation
        await this.getFeedbackAndAdjust();
        document.getElementById('drawingProgress').style.width = '100%';
    }
    
    async executeDrawingStep(step) {
        try {
            // Extract operation and parameters
            const { operation, params } = step;
            
            // Call the appropriate Canvas API method
            if (typeof this.canvasAPI[operation] === 'function') {
                // Convert params from array to arguments
                this.canvasAPI[operation](...params);
                console.log(`Executed: ${operation}(${params.join(', ')})`);
            } else {
                console.warn(`Unknown operation: ${operation}`);
            }
        } catch (error) {
            console.error('Error executing drawing step:', error);
        }
    }
    
    async getFeedbackAndAdjust() {
        if (!this.clipModel) return;
        
        // Get current canvas state
        const imageData = this.canvasAPI.getState();
        
        // Evaluate with CLIP
        const score = this.clipModel.scoreImage(imageData, this.currentPrompt);
        
        // Update feedback
        const feedbackEl = document.getElementById('modelFeedback');
        feedbackEl.textContent = `Similarity score: ${(score * 100).toFixed(1)}%`;
        
        // In a real implementation, we would adjust future drawing steps based on this feedback
        // For now, we just log the score
        console.log('CLIP feedback score:', score);
    }
    
    // Generate a drawing plan using compositional and evolutionary approach
    simulateDrawingPlan(prompt) {
        // Initialize with empty steps
        let bestDrawingSteps = [];
        let bestScore = -1;
        
        // Basic colors for our palette
        const colors = [
            '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', 
            '#FFFF00', '#FF00FF', '#00FFFF', '#FFA500', '#800080',
            '#A52A2A', '#808080', '#FFC0CB', '#008000', '#8B4513'
        ];
        
        // Define primitive shapes and elements for composition
        const primitives = {
            line: (x1, y1, x2, y2, color = '#000000', width = 2) => {
                return { 
                    operation: 'drawLine', 
                    params: [x1, y1, x2, y2, color, width]
                };
            },
            
            circle: (x, y, radius, color = '#000000', width = 2, fill = false) => {
                return { 
                    operation: 'drawCircle', 
                    params: [x, y, radius, color, width, fill]
                };
            },
            
            rectangle: (x, y, width, height, color = '#000000', lineWidth = 2, fill = false) => {
                return { 
                    operation: 'drawRectangle', 
                    params: [x, y, width, height, color, lineWidth, fill]
                };
            },
            
            polygon: (points, color = '#000000', width = 2) => {
                const steps = [];
                if (points.length < 2) return steps;
                
                for (let i = 0; i < points.length - 1; i++) {
                    steps.push({ 
                        operation: 'drawLine',
                        params: [points[i].x, points[i].y, points[i+1].x, points[i+1].y, color, width]
                    });
                }
                
                // Close the polygon
                steps.push({ 
                    operation: 'drawLine',
                    params: [points[points.length-1].x, points[points.length-1].y, points[0].x, points[0].y, color, width]
                });
                
                return steps;
            },
            
            // Create a curve using multiple line segments
            curve: (points, color = '#000000', width = 2) => {
                const steps = [];
                if (points.length < 2) return steps;
                
                for (let i = 0; i < points.length - 1; i++) {
                    steps.push({ 
                        operation: 'drawLine',
                        params: [points[i].x, points[i].y, points[i+1].x, points[i+1].y, color, width]
                    });
                }
                
                return steps;
            },
            
            // Create a filled region by drawing multiple adjacent lines
            filledRegion: (points, color = '#000000') => {
                const steps = [];
                if (points.length < 3) return steps;
                
                // Find top and bottom y values
                let minY = points[0].y;
                let maxY = points[0].y;
                
                for (let i = 1; i < points.length; i++) {
                    minY = Math.min(minY, points[i].y);
                    maxY = Math.max(maxY, points[i].y);
                }
                
                // Fill with horizontal lines
                for (let y = minY; y <= maxY; y += 2) {
                    const intersections = [];
                    
                    // Find all intersections with the polygon edges
                    for (let i = 0; i < points.length; i++) {
                        const j = (i + 1) % points.length;
                        const p1 = points[i];
                        const p2 = points[j];
                        
                        // Check if line segment crosses this y level
                        if ((p1.y <= y && p2.y > y) || (p2.y <= y && p1.y > y)) {
                            // Calculate x-intersection with this horizontal line
                            const x = p1.x + (y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y);
                            intersections.push(x);
                        }
                    }
                    
                    // Sort intersections by x
                    intersections.sort((a, b) => a - b);
                    
                    // Draw horizontal lines between pairs of intersections
                    for (let i = 0; i < intersections.length; i += 2) {
                        if (i + 1 < intersections.length) {
                            steps.push({ 
                                operation: 'drawLine',
                                params: [intersections[i], y, intersections[i+1], y, color, 1]
                            });
                        }
                    }
                }
                
                return steps;
            }
        };
        
        // Higher-level compositional elements
        const elements = {
            // Generate a path with random variations to simulate hand drawing
            sketchyLine: (x1, y1, x2, y2, color = '#000000', width = 2, jitter = 3, segments = 5) => {
                const steps = [];
                
                // Create points along the line with some randomness
                const points = [];
                points.push({x: x1, y: y1});
                
                for (let i = 1; i < segments; i++) {
                    const ratio = i / segments;
                    const midX = x1 + (x2 - x1) * ratio;
                    const midY = y1 + (y2 - y1) * ratio;
                    
                    // Add some random variation
                    const jitterX = (Math.random() - 0.5) * jitter;
                    const jitterY = (Math.random() - 0.5) * jitter;
                    
                    points.push({x: midX + jitterX, y: midY + jitterY});
                }
                
                points.push({x: x2, y: y2});
                
                // Create curve from points
                return primitives.curve(points, color, width);
            },
            
            // Create a filled circle with sketchy outline
            sketchyCircle: (x, y, radius, color = '#000000', outlineColor = '#000000', jitter = 5) => {
                const steps = [];
                
                // Add filled circle first
                steps.push(primitives.circle(x, y, radius, color, 1, true));
                
                // Add sketchy outline with multiple segments
                const segments = 12;
                const points = [];
                
                for (let i = 0; i <= segments; i++) {
                    const angle = (i / segments) * Math.PI * 2;
                    const jitterAmount = (Math.random() - 0.5) * jitter;
                    const r = radius + jitterAmount;
                    
                    points.push({
                        x: x + Math.cos(angle) * r,
                        y: y + Math.sin(angle) * r
                    });
                }
                
                // Create curve from points
                const outlineSteps = primitives.curve(points, outlineColor, 2);
                steps.push(...outlineSteps);
                
                return steps;
            },
            
            // Create a grid of random dots
            textureField: (x, y, width, height, color = '#000000', dotSize = 2, density = 0.2) => {
                const steps = [];
                const cols = Math.floor(width / (dotSize * 3));
                const rows = Math.floor(height / (dotSize * 3));
                
                for (let i = 0; i < cols; i++) {
                    for (let j = 0; j < rows; j++) {
                        // Only place dots with probability = density
                        if (Math.random() < density) {
                            const dotX = x + i * (width / cols) + (Math.random() - 0.5) * (width / cols);
                            const dotY = y + j * (height / rows) + (Math.random() - 0.5) * (height / rows);
                            
                            steps.push(primitives.circle(dotX, dotY, dotSize, color, 1, true));
                        }
                    }
                }
                
                return steps;
            },
            
            // Create a composition of random shapes
            abstractComposition: (x, y, width, height, colorPalette, complexity = 5) => {
                const steps = [];
                
                for (let i = 0; i < complexity; i++) {
                    const shapeType = Math.floor(Math.random() * 3);  // 0=circle, 1=rect, 2=polygon
                    const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
                    const fill = Math.random() > 0.5;
                    const shapeX = x + Math.random() * width;
                    const shapeY = y + Math.random() * height;
                    const shapeSize = Math.max(10, Math.random() * Math.min(width, height) * 0.4);
                    
                    if (shapeType === 0) {
                        // Circle
                        steps.push(primitives.circle(shapeX, shapeY, shapeSize/2, color, 2, fill));
                    } else if (shapeType === 1) {
                        // Rectangle
                        const rectW = shapeSize * (0.5 + Math.random());
                        const rectH = shapeSize * (0.5 + Math.random());
                        steps.push(primitives.rectangle(shapeX, shapeY, rectW, rectH, color, 2, fill));
                    } else {
                        // Polygon
                        const points = [];
                        const sides = 3 + Math.floor(Math.random() * 5);
                        for (let j = 0; j < sides; j++) {
                            const angle = (j / sides) * Math.PI * 2;
                            points.push({
                                x: shapeX + Math.cos(angle) * shapeSize/2,
                                y: shapeY + Math.sin(angle) * shapeSize/2
                            });
                        }
                        
                        if (fill) {
                            const filledRegion = primitives.filledRegion(points, color);
                            steps.push(...filledRegion);
                        } else {
                            const polygon = primitives.polygon(points, color, 2);
                            steps.push(...polygon);
                        }
                    }
                }
                
                return steps.flat();
            }
        };
        
        // Create multiple candidate drawings and score them
        const numCandidates = 3;
        const canvasWidth = 800;
        const canvasHeight = 600;
        const centerX = canvasWidth / 2;
        const centerY = canvasHeight / 2;
        
        // Parse the prompt for hints about what to draw
        const promptLower = prompt.toLowerCase();
        
        // Try to identify key subjects in the prompt
        const containsHuman = /person|human|man|woman|boy|girl|face|portrait|smile|figure/.test(promptLower);
        const containsNature = /landscape|tree|flower|mountain|river|ocean|forest|garden|plant|beach/.test(promptLower);
        const containsAnimal = /animal|cat|dog|bird|fish|horse|lion|tiger|bear/.test(promptLower);
        const containsObject = /house|building|car|chair|table|computer|phone|book|cup|food/.test(promptLower);
        const containsAbstract = /abstract|geometric|pattern|colorful|shape|random|art|design/.test(promptLower);
        
        // Identify colors in the prompt
        const colorMapping = {
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'purple': '#800080',
            'orange': '#FFA500',
            'pink': '#FFC0CB',
            'brown': '#A52A2A',
            'black': '#000000',
            'white': '#FFFFFF',
            'gray': '#808080',
            'grey': '#808080'
        };
        
        // Extract colors mentioned in the prompt
        const promptColors = [];
        Object.keys(colorMapping).forEach(colorName => {
            if (promptLower.includes(colorName)) {
                promptColors.push(colorMapping[colorName]);
            }
        });
        
        // If no colors specified, use default palette based on subject
        let palette = promptColors.length > 0 ? promptColors : colors;
        
        // For each candidate, generate a different approach to the drawing
        for (let candidateIdx = 0; candidateIdx < numCandidates; candidateIdx++) {
            const drawingSteps = [];
            const approach = candidateIdx % 3; // 0=minimal, 1=detailed, 2=abstract
            
            // Set initial line width and random color from palette
            drawingSteps.push({ 
                operation: 'setLineWidth', 
                params: [2 + Math.floor(Math.random() * 3)]
            });
            
            const primaryColor = palette[Math.floor(Math.random() * palette.length)];
            drawingSteps.push({ 
                operation: 'setColor', 
                params: [primaryColor]
            });
            
            // Create composition based on identified subjects
            if (containsHuman) {
                // Draw a human figure
                if (approach === 0) {
                    // Minimal stick figure
                    const headColor = promptColors.length > 0 ? promptColors[0] : '#000000';
                    const bodyColor = promptColors.length > 1 ? promptColors[1] : '#000000';
                    
                    // Draw head
                    drawingSteps.push(primitives.circle(centerX, centerY - 50, 30, headColor, 2, false));
                    
                    // Draw body
                    drawingSteps.push(primitives.line(centerX, centerY - 20, centerX, centerY + 50, bodyColor, 3));
                    
                    // Draw arms
                    drawingSteps.push(primitives.line(centerX, centerY, centerX - 40, centerY + 10, bodyColor, 3));
                    drawingSteps.push(primitives.line(centerX, centerY, centerX + 40, centerY + 10, bodyColor, 3));
                    
                    // Draw legs
                    drawingSteps.push(primitives.line(centerX, centerY + 50, centerX - 30, centerY + 120, bodyColor, 3));
                    drawingSteps.push(primitives.line(centerX, centerY + 50, centerX + 30, centerY + 120, bodyColor, 3));
                    
                } else if (approach === 1) {
                    // More detailed figure
                    const skinColor = promptColors.length > 0 ? promptColors[0] : '#FFC0CB';
                    const clothingColor = promptColors.length > 1 ? promptColors[1] : '#0000FF';
                    
                    // Draw head with filled circle
                    drawingSteps.push(primitives.circle(centerX, centerY - 60, 40, skinColor, 2, true));
                    
                    // Add face details
                    drawingSteps.push(primitives.circle(centerX - 15, centerY - 70, 5, '#000000', 1, true)); // left eye
                    drawingSteps.push(primitives.circle(centerX + 15, centerY - 70, 5, '#000000', 1, true)); // right eye
                    
                    // Add smile
                    const smilePoints = [];
                }
            }
}

// Export the class
window.AIAssistant = AIAssistant; 
    }
}