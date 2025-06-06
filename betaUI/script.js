document.addEventListener('DOMContentLoaded', function() {
    
    
    
    
    
    // Utility Functions
    function initializePageElements(selectors) {
        const elements = {};
        for (const [key, selector] of Object.entries(selectors)) {
            elements[key] = document.querySelector(selector);
        }
        return elements;
    }

    // File Upload Page Functionality (index.html)
    function initializeFileUpload() {
        const elements = {
            browsePdfButton: document.getElementById('browse-pdf'),
            uploadPdfButton: document.getElementById('upload-pdf'),
            uploadSection: document.getElementById('upload-section'),
            introScreen: document.getElementById('intro-screen'),
            mainContent: document.getElementById('main-content'),
            noPiiCheckbox: document.getElementById('no-pii-checkbox'),
            proceedButton: document.getElementById('proceed-button')
        };

        // Exit if not on upload page
        if (!elements.uploadSection) return;

        // Handle file upload functionality
        if (elements.browsePdfButton && elements.uploadPdfButton) {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.pdf';
            fileInput.style.display = 'none';
            document.body.appendChild(fileInput);

            const filenameDisplay = document.createElement('p');
            filenameDisplay.style.marginTop = '10px';
            filenameDisplay.style.color = '#666';

            elements.browsePdfButton.addEventListener('click', () => fileInput.click());

            fileInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    filenameDisplay.textContent = `Selected file: ${this.files[0].name}`;
                    elements.uploadSection.appendChild(filenameDisplay);
                    elements.uploadPdfButton.disabled = false;
                }
            });

            if (elements.introScreen && elements.mainContent) {
                elements.uploadPdfButton.addEventListener('click', function() {
                    elements.introScreen.style.display = 'none';
                    elements.mainContent.style.display = 'block';
                });
            }
        }

        // Handle no-PII checkbox functionality
        if (elements.noPiiCheckbox && elements.proceedButton) {
            elements.noPiiCheckbox.addEventListener('change', function() {
                elements.proceedButton.style.display = this.checked ? 'block' : 'none';
            });

            elements.proceedButton.addEventListener('click', function() {
                window.location.href = 'no-pii.html';
            });
        }
    }

    // PDF Drawing Tool Functionality (index.html)
    function initializePdfDrawingTool() {
        const elements = initializePageElements({
            editButton: '.edit',
            editMode: '.edit-mode',
            saveEditsButton: '.save-edits',
            cancelEditsButton: '.cancel-edits',
            pdfPreview: '.pdf-preview',
            canvas: '#pdf-canvas',
            textLayer: '#pdf-text-layer',
            editablePage: '.pdf-page.editable',
            toolHighlight: '.tool-highlight',
            toolDraw: '.tool-draw',
            clearAllButton: '.clear-all',
            undoButton: '.undo',
            redoButton: '.redo'
        });

        // Exit if not on PDF editing page
        if (!elements.editButton) return;

        // Initialize canvas context and state
        let ctx = elements.canvas ? elements.canvas.getContext('2d') : null;
        let isDrawing = false;
        let startX = 0;
        let startY = 0;
        let highlightMode = true;
        let undoStack = [];
        let redoStack = [];
        let savedCanvasState = null;

        // Canvas functions
        function clearCanvas() {
            if (elements.canvas && ctx) {
                ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
            }
        }

        function redrawCanvas() {
            clearCanvas();
            undoStack.forEach(action => {
                if (action.type === 'draw' && elements.canvas && ctx) {
                    ctx.putImageData(action.data, 0, 0);
                }
            });
        }

        // Canvas setup
        if (elements.canvas && ctx) {
            function setCanvasSize() {
                const editablePageRect = elements.editablePage.getBoundingClientRect();
                elements.canvas.width = editablePageRect.width;
                elements.canvas.height = editablePageRect.height;
                redrawCanvas();
            }

            setCanvasSize();
            window.addEventListener('resize', setCanvasSize);
        }

        // Drawing functions
        function startDrawing(e) {
            if (!highlightMode) {
                isDrawing = true;
                const rect = elements.canvas.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
            }
        }

        function drawRectangle(e) {
            if (!isDrawing || highlightMode) return;
            const rect = elements.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            if (elements.canvas && ctx) {
                ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
                redrawCanvas();
                
                ctx.beginPath();
                ctx.rect(startX, startY, x - startX, y - startY);
                ctx.fillStyle = 'rgba(128, 128, 128, 0.5)';
                ctx.fill();
            }
        }

        function endDrawing(e) {
            if (!highlightMode && isDrawing) {
                isDrawing = false;
                const rect = elements.canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                if (elements.canvas && ctx) {
                    ctx.beginPath();
                    ctx.rect(startX, startY, x - startX, y - startY);
                    ctx.fillStyle = 'rgba(128, 128, 128, 0.5)';
                    ctx.fill();
                    
                    undoStack.push({
                        type: 'draw',
                        data: ctx.getImageData(0, 0, elements.canvas.width, elements.canvas.height)
                    });
                    redoStack = [];
                }
            }
        }

        // Redaction functions
        function toggleRedaction(e) {
            if (highlightMode && e.target.parentElement === elements.textLayer) {
                e.target.classList.toggle('redacted');
                undoStack.push({type: 'toggle', element: e.target});
                redoStack = [];
            }
        }

        function copyRedactionsToEditMode() {
            const previewTextLayer = elements.pdfPreview.querySelector('.pdf-page');
            const editTextLayer = elements.textLayer;
            
            Array.from(previewTextLayer.children).forEach((previewChild, index) => {
                const editChild = editTextLayer.children[index];
                if (previewChild.classList.contains('redacted')) {
                    editChild.classList.add('redacted');
                } else {
                    editChild.classList.remove('redacted');
                }
            });
        }

        function applyRedactionsToPreview() {
            const previewTextLayer = elements.pdfPreview.querySelector('.pdf-page');
            const editTextLayer = elements.textLayer;
            
            Array.from(editTextLayer.children).forEach((editChild, index) => {
                const previewChild = previewTextLayer.children[index];
                if (editChild.classList.contains('redacted')) {
                    previewChild.classList.add('redacted');
                } else {
                    previewChild.classList.remove('redacted');
                }
            });
        }

        // Edit history functions
        function undo() {
            if (undoStack.length > 0) {
                const lastAction = undoStack.pop();
                redoStack.push(lastAction);
                if (lastAction.type === 'toggle') {
                    lastAction.element.classList.toggle('redacted');
                } else if (lastAction.type === 'draw') {
                    redrawCanvas();
                }
            }
        }

        function redo() {
            if (redoStack.length > 0) {
                const nextAction = redoStack.pop();
                undoStack.push(nextAction);
                if (nextAction.type === 'toggle') {
                    nextAction.element.classList.toggle('redacted');
                } else if (nextAction.type === 'draw') {
                    redrawCanvas();
                }
            }
        }

        function clearAll() {
            clearCanvas();
            undoStack = [];
            redoStack = [];
            Array.from(elements.textLayer.children).forEach(el => {
                el.classList.remove('redacted');
            });
        }

        // Display functions
        function displayEditedCanvas() {
            if (savedCanvasState) {
                const previewCanvas = document.createElement('canvas');
                previewCanvas.width = elements.canvas.width;
                previewCanvas.height = elements.canvas.height;
                previewCanvas.style.position = 'absolute';
                previewCanvas.style.top = '0';
                previewCanvas.style.left = '0';
                previewCanvas.style.width = '100%';
                previewCanvas.style.height = '100%';
                previewCanvas.style.pointerEvents = 'none';
                
                const previewCtx = previewCanvas.getContext('2d');
                previewCtx.putImageData(savedCanvasState, 0, 0);
                
                const previewPage = elements.pdfPreview.querySelector('.pdf-page');
                previewPage.style.position = 'relative';
                previewPage.appendChild(previewCanvas);
            }
        }

        // Event listeners for PDF editing tools
        if (elements.toolHighlight && elements.toolDraw) {
            elements.toolHighlight.addEventListener('click', function() {
                highlightMode = true;
                this.classList.add('active');
                elements.toolDraw.classList.remove('active');
                elements.editablePage.style.cursor = 'text';
                elements.textLayer.style.pointerEvents = 'auto';
                elements.canvas.style.pointerEvents = 'none';
            });

            elements.toolDraw.addEventListener('click', function() {
                highlightMode = false;
                this.classList.add('active');
                elements.toolHighlight.classList.remove('active');
                elements.editablePage.style.cursor = 'crosshair';
                elements.textLayer.style.pointerEvents = 'none';
                elements.canvas.style.pointerEvents = 'auto';
            });
        }

        // Event listeners for canvas
        if (elements.canvas) {
            elements.canvas.addEventListener('mousedown', startDrawing);
            elements.canvas.addEventListener('mousemove', drawRectangle);
            elements.canvas.addEventListener('mouseup', endDrawing);
            elements.canvas.addEventListener('mouseleave', endDrawing);
        }

        // Event listeners for text layer
        if (elements.textLayer) {
            elements.textLayer.addEventListener('click', toggleRedaction);
        }

        // Event listeners for buttons
        if (elements.clearAllButton) {
            elements.clearAllButton.addEventListener('click', clearAll);
        }
        if (elements.undoButton) {
            elements.undoButton.addEventListener('click', undo);
        }
        if (elements.redoButton) {
            elements.redoButton.addEventListener('click', redo);
        }
        if (elements.editButton) {
            elements.editButton.addEventListener('click', function() {
                elements.editMode.style.display = 'block';
                elements.pdfPreview.style.display = 'none';
                if (elements.canvas && ctx) {
                    setCanvasSize();
                }
                savedCanvasState = null;
                const previewCanvas = elements.pdfPreview.querySelector('canvas');
                if (previewCanvas) {
                    previewCanvas.remove();
                }
                copyRedactionsToEditMode();
            });
        }
        if (elements.saveEditsButton) {
            elements.saveEditsButton.addEventListener('click', function() {
                elements.editMode.style.display = 'none';
                elements.pdfPreview.style.display = 'block';
                
                if (elements.canvas && ctx) {
                    savedCanvasState = ctx.getImageData(0, 0, elements.canvas.width, elements.canvas.height);
                }
                
                applyRedactionsToPreview();
                displayEditedCanvas();
            });
        }
        if (elements.cancelEditsButton) {
            elements.cancelEditsButton.addEventListener('click', function() {
                elements.editMode.style.display = 'none';
                elements.pdfPreview.style.display = 'block';
                clearCanvas();
                undoStack = [];
                redoStack = [];
            });
        }
    }

    // Summary Page Functionality (summary.html)
    function initializeSummaryPage() {
        const elements = {
            progressSteps: document.getElementById('progress-steps'),
            summaryContent: document.getElementById('summary-content'),
            regenerateBtn: document.querySelector('.regenerate-btn'),
            summaryFeedback: document.getElementById('summary-feedback'),
            summaryNotes: document.getElementById('summary-notes'),
            saveBtn: document.querySelector('.save-btn'),
            copyBtn: document.querySelector('.copy-btn'),
            thumbsUpBtn: document.querySelector('.thumbs-up'),
            thumbsDownBtn: document.querySelector('.thumbs-down')
        };

        let current_narrative = ""
        let like = -1
        let folderName = ""
        let enhancedPdfReading = false
        let enhancedLlmReading = false

        function updateNarrativeHistory(narrative, feedback, notes, narrativeId, timestamp, testerName, like, folderName, enhancedPdfReading, enhancedLlmReading) {
            const user = (testerName) ? testerName : 'Anonymous';
          
            const newEntry = {
              narrativeId,
              timestamp,
              user,
              narrative,
              notes: notes || '',
              feedback: feedback || '',
              like: like || 0,
              folderName: folderName || '',
              marker: enhancedPdfReading || false,
              refine_approach: enhancedLlmReading || false
            };
          
            fetch('http://localhost:5000/save_history', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(newEntry)
            })
            .then(response => response.json())
            .then(data => {
              console.log('History saved:', data);
              renderNarrativeHistory(narrativeId, testerName); // re-fetch history after saving
            })
            .catch(err => console.error('Error saving history:', err));
        }
        
        // Render the narrative history log from localStorage into the ".generation-history" container.
        function renderNarrativeHistory(narrativeId, testerName) {
            
            fetch(`http://localhost:5000/get_history?narrativeId=${narrativeId}&testerName=${testerName}`)
              .then(response => response.json())
              .then(history => {
                console.log('History:', history);
                console.log('like:', like)
                
                const container = document.querySelector('.generation-history .history-entries');
                if (!container) return;
          
                // Clear existing entries.
                container.innerHTML = '';
          
                // Display the latest entry first.
                history.slice().reverse().forEach((entry, index) => {
                  const isActive = index === 0;
                  const statusClass = isActive ? 'active' : 'previous';
                  const statusText = isActive ? 'Currently Displayed' : 'Previous Version';
          
                  const entryHTML = `<div class="history-entry ${isActive ? 'active' : ''}">
                        <div class="entry-header">
                        <div class="entry-meta">
                            <span class="narrative-id">${entry.narrativeId}</span>
                            <span class="user">Tester Name: ${entry.user}</span>
                            <span class="timestamp">${entry.timestamp}</span>
                            <span class="status ${statusClass}">${statusText}</span>
                        </div>
                        </div>
                        <div class="entry-content">
                        <div class="narrative-text">${entry.narrative}</div>

                        ${entry.like !== -1 ? `
                            <div class="generation-notes">
                            <h4>User Feedback:</h4>
                            <div class="warning-message">
                                ${entry.like === 1? 'User <i class="fas fa-thumbs-up"></i> liked the narrative!' : 'User <i class="fas fa-thumbs-down"></i> disliked the narrative!'}
                            </div>
                            </div>
                        ` : ''}

                        ${entry.feedback ? `
                            <div class="generation-notes">
                            <h4>Narrative Feedback:</h4>
                            <div class="warning-message"><i class="fas fa-exclamation-triangle"></i> ${entry.feedback}</div>
                            </div>
                        ` : ''}

                        ${entry.notes ? `
                            <div class="generation-notes">
                            <h4>User Notes:</h4>
                            <div class="warning-message"><i class="fas fa-info-circle"></i> ${entry.notes}</div>
                            </div>
                        ` : ''}
                        
                        </div>
                    </div>
                  `;
                  container.innerHTML += entryHTML;
                });
              })
              .catch(err => console.error('Error retrieving history:', err));
        }

        function saveNotes() {
            const narrativeId = document.querySelector('.narrative-id');
            const timestamp = document.querySelector('.timestamp');
            const testerName = document.querySelector('.user').textContent.split(': ')[1];
            const notes = elements.summaryNotes.value;
            const feedback = elements.summaryFeedback.value;
            const narrative = current_narrative;


            // check if all fileds are filled 
            if (!narrativeId || !timestamp || !testerName || !notes || !narrative) {
                alert('Please fill in all fields before saving notes.');
                return;
            }

            updateNarrativeHistory(narrative, feedback, notes, narrativeId.textContent, timestamp.textContent, testerName, like, folderName, enhancedPdfReading, enhancedLlmReading);
        }

        function copyNarrative() {
            const narrative = current_narrative;
            navigator.clipboard.writeText(narrative);
        }

        function thumbsUp() {
            const narrativeId = document.querySelector('.narrative-id');
            const timestamp = document.querySelector('.timestamp');
            const testerName = document.querySelector('.user').textContent.split(': ')[1];
            const notes = elements.summaryNotes.value;
            const feedback = elements.summaryFeedback.value;
            const narrative = current_narrative;
            like = 1

            if (!narrativeId || !timestamp || !testerName || !narrative) {
                alert('Please fill in all fields before saving notes.');
                return;
            }

            updateNarrativeHistory(narrative, feedback, notes, narrativeId.textContent, timestamp.textContent, testerName, like, folderName, enhancedPdfReading, enhancedLlmReading)
        }

        function thumbsDown() {
            const narrativeId = document.querySelector('.narrative-id');
            const timestamp = document.querySelector('.timestamp');
            const testerName = document.querySelector('.user').textContent.split(': ')[1];
            const notes = elements.summaryNotes.value;
            const feedback = elements.summaryFeedback.value;
            const narrative = current_narrative;
            like = 0

            if (!narrativeId || !timestamp || !testerName || !narrative) {
                alert('Please fill in all fields before saving notes.');
                return;
            }

            updateNarrativeHistory(narrative, feedback, notes, narrativeId.textContent, timestamp.textContent, testerName, like, folderName, enhancedPdfReading, enhancedLlmReading)
        }

        // Exit if not on summary page
        if (!elements.progressSteps) return;

        // const urlParams = new URLSearchParams(window.location.search);
        // const testerName = decodeURIComponent(urlParams.get('testerName') || '');
        // const folderName = decodeURIComponent(urlParams.get('folderName') || '');
        // const caseNumber = folderName.split('_')[1];
        // console.log(caseNumber, testerName, folderName);

        // Retrieve full data from sessionStorage
        let caseData;
        try {
            caseData = JSON.parse(sessionStorage.getItem('caseSelectionData') || '{}');
        } catch (error) {
            console.error('Error parsing case data from sessionStorage:', error);
            caseData = {
            };
        }

        console.log('Case data:', caseData);
        folderName = caseData.folderName
        enhancedPdfReading = caseData.enhancedPdfReading
        enhancedLlmReading = caseData.enhancedLlmReading

        async function generateNarrative() {
            try {
                
                if (enhancedLlmReading) {
                    // Make Refine API call to localhost
                    const response = await fetch('http://localhost:5000/generate_narrative_refined', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            "case": caseData.caseNumber,
                            "files": caseData.selectedFiles,
                            "folderName": caseData.folderName,
                            "marker" : enhancedPdfReading
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    return data.narrative;
                }else{
                    // Make Normal API call to localhost
                    const response = await fetch('http://localhost:5000/generate_narrative', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            "case": caseData.caseNumber,
                            "files": caseData.selectedFiles,
                            "folderName": caseData.folderName,
                            "marker" : enhancedPdfReading
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    return data.narrative;
                }

            } catch (error) {
                console.error('Error generating narrative:', error);
                throw error;
            }
            
        }

        async function generateNarrativeRevision() {
            try {

                const old_narrative = current_narrative
                const feedback = elements.summaryFeedback.value

                // console.log(old_narrative, feedback)

                if (enhancedLlmReading) {
                    // Make Refine API call to localhost
                    const response = await fetch('http://localhost:5000/generate_narrative_revision_refined', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            "case": caseData.caseNumber,
                            "files": caseData.selectedFiles,
                            "folderName": caseData.folderName,
                            "narrative": old_narrative,
                            "feedback": feedback,
                            "marker" : enhancedPdfReading
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    return data.narrative;
                }else{
                    // Make Normal API call to localhost
                    const response = await fetch('http://localhost:5000/generate_narrative_revision', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            "case": caseData.caseNumber,
                            "files": caseData.selectedFiles,
                            "folderName": caseData.folderName,
                            "narrative": old_narrative,
                            "feedback": feedback,
                            "marker" : enhancedPdfReading
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    return data.narrative;
                }
            } catch (error) {
                console.error('Error generating narrative:', error);
                throw error;
            }
        }

        function updateProgressSteps(currentStep) {
            const steps = elements.progressSteps.querySelectorAll('.step');
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                step.classList.add('completed');
                step.querySelector('i').classList.remove('fa-spinner', 'fa-spin');
                step.querySelector('i').classList.add('fa-check');
            }
        }

        async function startGeneratingSummary() {
            if (!elements.progressSteps || !elements.summaryContent) return;

            // const notesLoading = document.getElementById('notes-loading');
            // const notesContent = document.getElementById('notes-content');

            // Generate new narrative ID and timestamp
            const narrativeId = document.querySelector('.narrative-id');
            const timestamp = document.querySelector('.timestamp');
            if (narrativeId && timestamp) {
                const date = new Date();
                const id = `NAR-${date.getFullYear()}-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;
                const timeString = date.toLocaleString('en-US', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    timeZone: 'America/Anchorage',
                    hour12: false
                }) + ' AKST';

                narrativeId.textContent = `Narrative ID: ${id}`;
                timestamp.textContent = `Generated: ${timeString}`;
            }

            // Reset UI state
            elements.progressSteps.style.display = 'block';
            elements.summaryContent.value = '';
            // notesContent.style.display = 'none';
            // notesLoading.style.display = 'flex';

            // Reset progress steps
            const steps = elements.progressSteps.querySelectorAll('.step');
            steps.forEach(step => {
                step.classList.remove('completed');
                const icon = step.querySelector('i');
                icon.classList.remove('fa-check');
                icon.classList.add('fa-spinner', 'fa-spin');
            });

            try {
                for (let i = 0; i < 2; i++) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    updateProgressSteps(i);
                }

                // Make actual API call during step 4
                const narrative = await generateNarrative();
                console.log('Narrative:', narrative);
                updateProgressSteps(2);

                // Show the narrative
                elements.summaryContent.value = narrative;
                current_narrative = narrative

                // console.log(narrative, elements.summaryFeedback.value, narrativeId, timestamp, caseData.testerName)

                updateNarrativeHistory(narrative, elements.summaryFeedback.value, elements.summaryNotes.value, narrativeId.textContent, timestamp.textContent, caseData.testerName, like, folderName, enhancedPdfReading, enhancedLlmReading)

                // Complete final step
                for (let i = 3; i < steps.length; i++) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    updateProgressSteps(i);
                }

                // Show notes 1 second after narrative appears
                // setTimeout(() => {
                //     notesLoading.style.display = 'none';
                //     notesContent.style.display = 'block';
                // }, 1000);

            } catch (error) {
                // Handle error state
                elements.summaryContent.value = 'Error generating narrative. Please try again.';
                console.error('Error:', error);
            }
        }

        async function startGeneratingRevision() {
            if (!elements.progressSteps || !elements.summaryContent) return;

            const timestamp = document.querySelector('.timestamp');
            const narrativeId = document.querySelector('.narrative-id');
            if (timestamp) {
                const date = new Date();
                const timeString = date.toLocaleString('en-US', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    timeZone: 'America/Anchorage',
                    hour12: false
                }) + ' AKST';

                timestamp.textContent = `Generated: ${timeString}`;
            }

            // Reset UI state
            elements.progressSteps.style.display = 'block';
            elements.summaryContent.value = '';

            // Reset progress steps
            const steps = elements.progressSteps.querySelectorAll('.step');
            steps.forEach(step => {
                step.classList.remove('completed');
                const icon = step.querySelector('i');
                icon.classList.remove('fa-check');
                icon.classList.add('fa-spinner', 'fa-spin');
            });

            try {
                for (let i = 0; i < 2; i++) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    updateProgressSteps(i);
                }

                // Make actual API call during step 4
                const narrative = await generateNarrativeRevision();
                current_narrative = narrative

                updateNarrativeHistory(narrative, elements.summaryFeedback.value, elements.summaryNotes.value, narrativeId.textContent, timestamp.textContent, caseData.testerName, like, folderName, enhancedPdfReading, enhancedLlmReading)
                updateProgressSteps(2);

                // Show the narrative
                elements.summaryContent.value = narrative;

                // Complete final step
                for (let i = 3; i < steps.length; i++) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    updateProgressSteps(i);
                }

            } catch (error) {
                // Handle error state
                elements.summaryContent.value = 'Error generating narrative. Please try again.';
                console.error('Error:', error);
            }
        }

        // Initialize summary generation
        startGeneratingSummary();

        // Add regenerate button functionality
        if (elements.regenerateBtn) {
            elements.regenerateBtn.addEventListener('click', startGeneratingRevision);
        }

        if (elements.saveBtn) {
            elements.saveBtn.addEventListener('click', saveNotes);
        }

        if (elements.copyBtn) {
            elements.copyBtn.addEventListener('click', copyNarrative);
        }

        if (elements.thumbsUpBtn) {
            elements.thumbsUpBtn.addEventListener('click', thumbsUp);
        }

        if (elements.thumbsDownBtn) {
            elements.thumbsDownBtn.addEventListener('click', thumbsDown);
        }
        
    }

    // Common UI Elements (shared across pages)
    function initializeCommonElements() {
        const cautionBanner = document.getElementById('caution-banner');
        const understandBtn = document.querySelector('.understand-btn');

        if (understandBtn && cautionBanner) {
            understandBtn.addEventListener('click', () => {
                cautionBanner.style.display = 'none';
            });
        }
    }

    function acknowledgeBanner() {
        const cautionBanner = document.getElementById('caution-banner');
        cautionBanner.style.display = 'none';
    }

    // Initialize all functionality
    // localStorage.clear();
    initializeFileUpload();
    initializePdfDrawingTool();
    initializeSummaryPage();
    initializeCommonElements();
});