document.addEventListener('DOMContentLoaded', function() {
    // Remove or comment out the lines related to uploadButton
    const uploadButton = document.getElementById('upload-pdf');
    const introScreen = document.getElementById('intro-screen');
    const mainContent = document.getElementById('main-content');

    if (uploadButton) {
        uploadButton.addEventListener('click', function() {
            introScreen.style.display = 'none';
            mainContent.style.display = 'block';
        });
    }

    const editButton = document.querySelector('.edit');
    const editMode = document.querySelector('.edit-mode');
    const saveEditsButton = document.querySelector('.save-edits');
    const cancelEditsButton = document.querySelector('.cancel-edits');
    const pdfPreview = document.querySelector('.pdf-preview');
    const canvas = document.getElementById('pdf-canvas');
    let ctx;
    if (canvas) {
        ctx = canvas.getContext('2d');
    }
    const textLayer = document.getElementById('pdf-text-layer');
    const editablePage = document.querySelector('.pdf-page.editable');

    let isDrawing = false;
    let startX = 0;
    let startY = 0;
    let highlightMode = true;
    let undoStack = [];
    let redoStack = [];

    let savedCanvasState = null;

    if (canvas && ctx) {
        function setCanvasSize() {
            const editablePageRect = editablePage.getBoundingClientRect();
            canvas.width = editablePageRect.width;
            canvas.height = editablePageRect.height;
            console.log('Canvas size set to:', canvas.width, 'x', canvas.height);
            redrawCanvas(); // Add this line to redraw after resizing
        }

        setCanvasSize();
        window.addEventListener('resize', setCanvasSize);
    }

    // Only add event listener if editButton exists
    if (editButton) {
        editButton.addEventListener('click', function() {
            editMode.style.display = 'block';
            pdfPreview.style.display = 'none';
            if (canvas && ctx) {
                setCanvasSize(); // Add this line
            }
            // Clear the saved canvas state
            savedCanvasState = null;
            // Remove the preview canvas if it exists
            const previewCanvas = pdfPreview.querySelector('canvas');
            if (previewCanvas) {
                previewCanvas.remove();
            }
            // Copy redaction states from preview to edit mode
            copyRedactionsToEditMode();
        });
    }

    saveEditsButton.addEventListener('click', function() {
        editMode.style.display = 'none';
        pdfPreview.style.display = 'block';
        
        // Save the current canvas state
        if (canvas && ctx) {
            savedCanvasState = ctx.getImageData(0, 0, canvas.width, canvas.height);
        }
        
        // Apply redactions to the preview
        applyRedactionsToPreview();
        
        // Display the edited canvas in the preview
        displayEditedCanvas();
    });

    cancelEditsButton.addEventListener('click', function() {
        editMode.style.display = 'none';
        pdfPreview.style.display = 'block';
        clearCanvas();
        undoStack = [];
        redoStack = [];
    });

    document.querySelector('.tool-highlight').addEventListener('click', function() {
        highlightMode = true;
        this.classList.add('active');
        document.querySelector('.tool-draw').classList.remove('active');
        editablePage.style.cursor = 'text';
        textLayer.style.pointerEvents = 'auto';
        canvas.style.pointerEvents = 'none';
    });

    document.querySelector('.tool-draw').addEventListener('click', function() {
        highlightMode = false;
        this.classList.add('active');
        document.querySelector('.tool-highlight').classList.remove('active');
        editablePage.style.cursor = 'crosshair';
        textLayer.style.pointerEvents = 'none';
        canvas.style.pointerEvents = 'auto';
    });

    document.querySelector('.undo').addEventListener('click', undo);
    document.querySelector('.redo').addEventListener('click', redo);
    document.querySelector('.clear-all').addEventListener('click', clearAll);

    textLayer.addEventListener('click', toggleRedaction);
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', drawRectangle);
    canvas.addEventListener('mouseup', endDrawing);
    canvas.addEventListener('mouseleave', endDrawing);

    function toggleRedaction(e) {
        if (highlightMode && e.target.parentElement === textLayer) {
            e.target.classList.toggle('redacted');
            undoStack.push({type: 'toggle', element: e.target});
            redoStack = [];
        }
    }

    function startDrawing(e) {
        if (!highlightMode) {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
        }
    }

    function drawRectangle(e) {
        if (!isDrawing || highlightMode) return;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (canvas && ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
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
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            if (canvas && ctx) {
                ctx.beginPath();
                ctx.rect(startX, startY, x - startX, y - startY);
                ctx.fillStyle = 'rgba(128, 128, 128, 0.5)';
                ctx.fill();
                
                undoStack.push({type: 'draw', data: ctx.getImageData(0, 0, canvas.width, canvas.height)});
                redoStack = [];
            }
        }
    }

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
        Array.from(textLayer.children).forEach(el => {
            el.classList.remove('redacted');
        });
    }

    function clearCanvas() {
        if (canvas && ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    function redrawCanvas() {
        clearCanvas();
        undoStack.forEach(action => {
            if (action.type === 'draw') {
                if (canvas && ctx) {
                    ctx.putImageData(action.data, 0, 0);
                }
            }
        });
    }

    function applyRedactionsToPreview() {
        const previewTextLayer = pdfPreview.querySelector('.pdf-page');
        const editTextLayer = document.getElementById('pdf-text-layer');
        
        // Copy redaction states from edit mode to preview
        Array.from(editTextLayer.children).forEach((editChild, index) => {
            const previewChild = previewTextLayer.children[index];
            if (editChild.classList.contains('redacted')) {
                previewChild.classList.add('redacted');
            } else {
                previewChild.classList.remove('redacted');
            }
        });
    }

    function displayEditedCanvas() {
        if (savedCanvasState) {
            // Create a new canvas for the preview
            const previewCanvas = document.createElement('canvas');
            previewCanvas.width = canvas.width;
            previewCanvas.height = canvas.height;
            previewCanvas.style.position = 'absolute';
            previewCanvas.style.top = '0';
            previewCanvas.style.left = '0';
            previewCanvas.style.width = '100%';
            previewCanvas.style.height = '100%';
            previewCanvas.style.pointerEvents = 'none';
            
            const previewCtx = previewCanvas.getContext('2d');
            previewCtx.putImageData(savedCanvasState, 0, 0);
            
            // Add the canvas to the preview
            const previewPage = pdfPreview.querySelector('.pdf-page');
            previewPage.style.position = 'relative';
            previewPage.appendChild(previewCanvas);
        }
    }

    function copyRedactionsToEditMode() {
        const previewTextLayer = pdfPreview.querySelector('.pdf-page');
        const editTextLayer = document.getElementById('pdf-text-layer');
        
        Array.from(previewTextLayer.children).forEach((previewChild, index) => {
            const editChild = editTextLayer.children[index];
            if (previewChild.classList.contains('redacted')) {
                editChild.classList.add('redacted');
            } else {
                editChild.classList.remove('redacted');
            }
        });
    }

    const checkbox = document.getElementById('no-pii-checkbox');
    const proceedButton = document.getElementById('proceed-button');

    if (checkbox && proceedButton) {
        checkbox.addEventListener('change', function() {
            proceedButton.style.display = this.checked ? 'block' : 'none';
        });

        proceedButton.addEventListener('click', function() {
            window.location.href = 'no-pii.html';
        });
    }

    // Add this new function to handle the remove and upload functionality
    function setupDocumentBoxes() {
        const documentBoxes = document.querySelectorAll('.document-box');
        
        documentBoxes.forEach(box => {
            const removeButton = box.querySelector('.remove-file');
            const selectFile = box.querySelector('.select-file');
            const fileName = box.querySelector('.file-name');
            
            if (removeButton) {
                removeButton.addEventListener('click', function() {
                    // Hide the file name, checkbox, and remove button
                    fileName.style.display = 'none';
                    selectFile.style.display = 'none';
                    removeButton.style.display = 'none';
                    
                    // Create and add the upload button
                    const uploadButton = document.createElement('button');
                    uploadButton.textContent = 'Upload';
                    uploadButton.className = 'upload-btn';
                    uploadButton.style.backgroundColor = '#4CAF50';
                    uploadButton.style.color = 'white';
                    uploadButton.style.border = 'none';
                    uploadButton.style.padding = '10px 20px';
                    uploadButton.style.borderRadius = '5px';
                    uploadButton.style.cursor = 'pointer';
                    uploadButton.style.marginTop = '10px';
                    
                    box.appendChild(uploadButton);
                    
                    // Add click event to the upload button
                    uploadButton.addEventListener('click', function() {
                        // Here you would typically trigger a file upload dialog
                        // For this mockup, we'll just simulate restoring the original state
                        fileName.style.display = 'block';
                        selectFile.style.display = 'flex';
                        removeButton.style.display = 'block';
                        uploadButton.remove();
                    });
                });
            }
        });
    }

    // Call the setup function
    setupDocumentBoxes();

    // Add new functions for summary generation
    function startGeneratingSummary() {
        const progressSteps = document.getElementById('progress-steps');
        const summaryBox = document.querySelector('.summary-box');

        // Show the progress steps
        if (progressSteps) {
            progressSteps.style.display = 'flex';
        }
        
        // Start the progress simulation
        simulateProgress();
        
        // Add your logic for generating the summary here
        console.log('Generate Summary started');
        
        // After 4 seconds (when all steps are complete), show the summary
        setTimeout(function() {
            if (progressSteps) {
                progressSteps.style.display = 'none';
            }
            if (summaryBox) {
                summaryBox.style.display = 'block';
            }
        }, 4000);
    }

    function simulateProgress() {
        const steps = document.querySelectorAll('#progress-steps .step');
        let currentStep = 0;

        function updateStep() {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                step.classList.add('completed');
                step.querySelector('i').classList.remove('fa-spinner', 'fa-spin');
                step.querySelector('i').classList.add('fa-check');
                currentStep++;
                setTimeout(updateStep, 1000); // Wait 1 second before updating the next step
            }
        }

        updateStep();
    }

    // Function to initialize the summary page
    function initSummaryPage() {
        if (document.getElementById('progress-steps')) {
            startGeneratingSummary();
        }

        // Add event listener for regenerate button if it exists
        const regenerateBtn = document.querySelector('.regenerate-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', startGeneratingSummary);
        }

        // Add event listeners for feedback buttons if they exist
        const feedbackBtns = document.querySelectorAll('.feedback-btn');
        feedbackBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                console.log('Feedback button clicked:', this.classList);
            });
        });

        // Add event listener for copy button if it exists
        const copyBtn = document.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', function() {
                const summaryContent = document.getElementById('summary-content');
                if (summaryContent) {
                    const range = document.createRange();
                    range.selectNode(summaryContent);
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                    document.execCommand('copy');
                    window.getSelection().removeAllRanges();
                    console.log('Summary copied to clipboard');
                }
            });
        }
    }

    // Call initSummaryPage when the DOM is fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSummaryPage);
    } else {
        initSummaryPage();
    }
});