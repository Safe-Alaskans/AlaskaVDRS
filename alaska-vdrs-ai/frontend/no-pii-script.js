document.addEventListener('DOMContentLoaded', function() {
    function initializeNoPii() {
        const elements = {
            folderInput: document.getElementById('folder-input'),
            folderName: document.getElementById('folder-name'),
            fileCount: document.getElementById('file-count'),
            selectedFolderInfo: document.getElementById('selected-folder-info'),
            fileListHeader: document.querySelector('.file-list-header'),
            documentGrid: document.getElementById('dynamic-document-grid'),
            selectionInfo: document.querySelector('.selection-info'),
            generateSummaryButton: document.getElementById('generate-summary'),
            testerName: document.getElementById('tester-name'),
            enhancedPdfToggle: document.getElementById('enhanced-pdf-toggle'),
            enhancedLlmToggle: document.getElementById('enhanced-llm-toggle'),
        }
        
        const selectedFiles = [];
        
        elements.folderInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);

            if (files.length > 0) {

                const folderPath = files[0].webkitRelativePath;
                const folderName = folderPath.split('/')[0];

                elements.folderName.textContent = folderName;
                elements.fileCount.textContent = files.length;
                elements.selectedFolderInfo.style.display = 'flex';
                elements.selectionInfo.style.display = 'block';

                 // Show file list header
                elements.fileListHeader.style.display = 'block';

                // Clear existing document grid
                elements.documentGrid.innerHTML = '';

                // Process only the files directly in the selected folder (not in subfolders)
                const directFiles = files.filter(file => {
                    const pathParts = file.webkitRelativePath.split('/');
                    return pathParts.length === 2; // Only include files directly in the selected folder
                });
                
                directFiles.forEach(file => {
                    selectedFiles.push(file);

                    // Determine file icon based on extension
                    let iconClass = 'fas fa-file';
                    const extension = file.name.split('.').pop().toLowerCase();
                    
                    if (['pdf'].includes(extension)) {
                        iconClass = 'fas fa-file-pdf';
                    } else if (['doc', 'docx'].includes(extension)) {
                        iconClass = 'fas fa-file-word';
                    } else if (['xls', 'xlsx', 'csv'].includes(extension)) {
                        iconClass = 'fas fa-file-excel';
                    } else if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
                        iconClass = 'fas fa-file-image';
                    } else if (['txt', 'rtf'].includes(extension)) {
                        iconClass = 'fas fa-file-alt';
                    }
                    
                    const fileBox = document.createElement('div');
                    fileBox.className = 'document-box';
                    fileBox.innerHTML = `
                        <i class="${iconClass} file-icon"></i>
                        <p class="file-name">${file.name}</p>
                        <label class="select-file">
                            <input type="checkbox" name="selected_files" value="${file.name}" checked>
                            <span class="checkmark"></span>
                            Include File
                        </label>
                    `;
                    
                    elements.documentGrid.appendChild(fileBox);
                });
                    
            } else {
                elements.folderName.textContent = 'No files selected';
            }
        });  


        elements.generateSummaryButton.addEventListener('click', async function() {
            const testerName = elements.testerName.value;
            if (!testerName) {
                alert('Please enter your name before proceeding.');
                return;
            }
            
            // Check if folder is selected
            if (elements.folderName.textContent === 'None') {
                alert('Please select a case folder before proceeding.');
                return;
            }

            
            if (selectedFiles.length === 0) {
                alert('Please select at least one file to proceed.');
                return;
            }
            
            // Get folder name to pass to summary page
            const folderName = elements.folderName.textContent;
            const caseNumber = folderName.split('_')[1] || ''; // Extract case number if available
            
            // Process selected files - read their data
            const filePromises = selectedFiles.map(file => {
                
                return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onload = (e) => {
                            resolve({
                                name: file.name,
                                type: file.type,
                                size: file.size,
                                data: e.target.result, // Base64 encoded file data
                                lastModified: file.lastModified
                            });
                        };
                        reader.readAsDataURL(file);
                    });
            });

            try {
                // Wait for all file reads to complete
                const fileDataArray = await Promise.all(filePromises);

                // Get enhanced PDF reading toggle state
                const enhancedPdfReading = elements.enhancedPdfToggle.checked;
                const enhancedLlmReading = elements.enhancedLlmToggle.checked;

                // Prepare data to pass to summary page
                const data = {
                    testerName: testerName,
                    folderName: folderName,
                    caseNumber: caseNumber,
                    selectedFiles: fileDataArray,
                    timestamp: new Date().toISOString(),
                    enhancedPdfReading: enhancedPdfReading,
                    enhancedLlmReading: enhancedLlmReading
                };
                
                // Store data in sessionStorage
                sessionStorage.setItem('caseSelectionData', JSON.stringify(data));
                
                // Pass tester name and folder name via URL parameters instead of localStorage
                const url = new URL('summary.html', window.location.href);
                // url.searchParams.append('testerName', encodeURIComponent(testerName));
                // url.searchParams.append('folderName', encodeURIComponent(folderName));
                
                // Navigate to summary page with parameters
                window.location.href = url.toString();
            } catch (error) {
                console.error('Error processing files:', error);
                alert('An error occurred while processing the files. Please try again.');
            }
        });
    }

    initializeNoPii();
});