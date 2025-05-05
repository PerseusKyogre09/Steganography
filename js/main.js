/**
 * Cicada Steganography Web Application
 * Main UI logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const encodeImageInput = document.getElementById('encode-image-input');
    const encodeImageName = document.getElementById('encode-image-name');
    const encodePreviewImage = document.getElementById('encode-preview-image');
    const encodePreviewPlaceholder = document.getElementById('encode-preview-placeholder');
    const encodeModeRadios = document.querySelectorAll('input[name="encode-mode"]');
    const messageContainer = document.getElementById('message-input-container');
    const fileContainer = document.getElementById('file-input-container');
    const messageInput = document.getElementById('message-input');
    const encodeFileInput = document.getElementById('encode-file-input');
    const encodeFileName = document.getElementById('encode-file-name');
    const fileInfo = document.getElementById('file-info');
    const encodeBtn = document.getElementById('encode-btn');
    const decodeImageInput = document.getElementById('decode-image-input');
    const decodeImageName = document.getElementById('decode-image-name');
    const decodePreviewImage = document.getElementById('decode-preview-image');
    const decodePreviewPlaceholder = document.getElementById('decode-preview-placeholder');
    const decodeBtn = document.getElementById('decode-btn');
    const imageInfo = document.getElementById('image-info');
    const statusText = document.getElementById('status-text');
    const modal = document.getElementById('result-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const closeModal = document.querySelector('.close-modal');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    
    // Current state
    let encodeMode = 'message';
    let encodeImageElement = null;
    let decodeImageElement = null;
    let selectedFile = null;
    
    // Mobile-specific state variables
    let isMobile = window.matchMedia("(max-width: 768px)").matches;
    let hasTouchStarted = false;
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(`${button.dataset.tab}-tab`).classList.add('active');
        });
    });
    
    // File input handlers with better mobile support
    document.querySelectorAll('.file-input').forEach(container => {
        const input = container.querySelector('input[type="file"]');
        const button = container.querySelector('.browse-btn');
        
        // Better handling for touch events
        button.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent double-tap zoom on mobile
            input.click();
        });
        
        // Handle the fact that some mobile browsers don't trigger change on capture
        input.addEventListener('click', () => {
            hasTouchStarted = true;
        });
        
        // Focus handling for accessibility
        button.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                input.click();
            }
        });
    });
    
    // Encode mode selection
    encodeModeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            encodeMode = radio.value;
            
            if (encodeMode === 'message') {
                messageContainer.classList.remove('hidden');
                fileContainer.classList.add('hidden');
            } else {
                messageContainer.classList.add('hidden');
                fileContainer.classList.remove('hidden');
            }
        });
    });
    
    // Handle encode image selection with mobile improvements
    encodeImageInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            const file = event.target.files[0];
            
            if (file.type !== 'image/png') {
                updateStatus('Error: Only PNG images are supported');
                return;
            }
            
            encodeImageName.textContent = isMobile && file.name.length > 20 ? 
                file.name.substring(0, 18) + '...' : file.name;
            updatePreview(file, encodePreviewImage, encodePreviewPlaceholder);
            
            // Create Image element for encoding
            const reader = new FileReader();
            reader.onload = (e) => {
                encodeImageElement = new Image();
                encodeImageElement.onload = () => {
                    // Calculate and display capacity
                    const maxBytes = Math.floor((encodeImageElement.width * encodeImageElement.height * 3 * BITS_PER_CHANNEL) / 8);
                    const capacityKb = (maxBytes/1024).toFixed(1);
                    
                    // Simplified display for small screens
                    if (isMobile) {
                        imageInfo.textContent = `Max: ${capacityKb} KB`;
                    } else {
                        imageInfo.textContent = `Size: ${encodeImageElement.width}x${encodeImageElement.height} pixels | Max capacity: ${capacityKb} KB`;
                    }
                };
                encodeImageElement.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Handle file selection for encoding
    encodeFileInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            selectedFile = event.target.files[0];
            encodeFileName.textContent = isMobile && selectedFile.name.length > 20 ? 
                selectedFile.name.substring(0, 18) + '...' : selectedFile.name;
            
            // Update file info
            const extension = selectedFile.name.split('.').pop() || 'Unknown';
            let sizeText = '';
            
            if (selectedFile.size < 1024) {
                sizeText = `${selectedFile.size} bytes`;
            } else if (selectedFile.size < 1024 * 1024) {
                sizeText = `${(selectedFile.size / 1024).toFixed(1)} KB`;
            } else {
                sizeText = `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`;
            }
            
            // Simplified display for mobile
            if (isMobile) {
                fileInfo.textContent = `${extension.toUpperCase()} | ${sizeText}`;
            } else {
                fileInfo.textContent = `File: ${selectedFile.name} | Type: ${extension.toUpperCase()} | Size: ${sizeText}`;
            }
            
            // Warn if file is too large
            if (selectedFile.size > 5 * 1024 * 1024) {
                fileInfo.textContent += (isMobile ? ' (Large)' : ' (Large file - encoding may be slow)');
            }
        }
    });
    
    // Handle decode image selection
    decodeImageInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            const file = event.target.files[0];
            
            if (file.type !== 'image/png') {
                updateStatus('Error: Only PNG images are supported');
                return;
            }
            
            decodeImageName.textContent = isMobile && file.name.length > 20 ? 
                file.name.substring(0, 18) + '...' : file.name;
            updatePreview(file, decodePreviewImage, decodePreviewPlaceholder);
            
            // Create Image element for decoding
            const reader = new FileReader();
            reader.onload = (e) => {
                decodeImageElement = new Image();
                decodeImageElement.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Update image preview with optimizations for mobile
    function updatePreview(file, imgElement, placeholder) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imgElement.onload = () => {
                placeholder.classList.add('hidden');
                imgElement.classList.remove('hidden');
            };
            imgElement.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    // Encode button with improved mobile experience
    encodeBtn.addEventListener('click', async () => {
        // Blur active element to hide mobile keyboard if open
        if (document.activeElement) {
            document.activeElement.blur();
        }
        
        if (!encodeImageElement) {
            updateStatus('Please select an image first');
            return;
        }
        
        let dataToEncode;
        
        try {
            showLoading('Preparing data...');
            
            if (encodeMode === 'message') {
                const message = messageInput.value.trim();
                if (!message) {
                    updateStatus('Please enter a message to encode');
                    hideLoading();
                    return;
                }
                
                dataToEncode = prepareTextData(message);
            } else {
                if (!selectedFile) {
                    updateStatus('Please select a file to encode');
                    hideLoading();
                    return;
                }
                
                // Check file size against capacity
                const maxBytes = Math.floor((encodeImageElement.width * encodeImageElement.height * 3 * BITS_PER_CHANNEL) / 8);
                if (selectedFile.size > maxBytes * 0.7) { // 70% as a safety margin due to markers and compression overhead
                    if (!confirm(`The selected file (${(selectedFile.size/1024).toFixed(1)} KB) might be too large for this image (max ${(maxBytes/1024).toFixed(1)} KB). Try anyway?`)) {
                        hideLoading();
                        return;
                    }
                }
                
                dataToEncode = await prepareFileData(selectedFile);
            }
            
            updateStatus('Encoding data...');
            showLoading('Encoding data into image... This might take a moment for large files.');
            
            const encodedImageBlob = await encodeDataToImage(encodeImageElement, dataToEncode, true);
            
            // Create download link for the encoded image
            const url = URL.createObjectURL(encodedImageBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'encoded_' + (encodeImageName.textContent || 'image.png');
            
            hideLoading();
            
            // Show success message with custom modal
            openModal('Encoding Successful', `
                <p>Your data has been successfully encoded into the image!</p>
                <p>Click the button below to download the encoded image:</p>
                <button id="download-encoded-image" class="primary-btn" style="margin: 15px 0;">Download Encoded Image</button>
            `);
            
            // Add event listener to the download button
            document.getElementById('download-encoded-image').addEventListener('click', () => {
                // Special handling for iOS Safari which doesn't support automatic downloads
                if (isIOS()) {
                    alert("Your browser doesn't support automatic downloads. The image will open in a new tab - please save it from there.");
                    window.open(url, '_blank');
                } else {
                    a.click();
                }
                updateStatus('Encoded image downloaded');
            });
            
            // Cleanup
            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 60000); // Give user 1 minute to download
            
        } catch (error) {
            hideLoading();
            updateStatus(`Error: ${error.message}`);
            alert(`Encoding failed: ${error.message}`);
        }
    });
    
    // Decode button with improved mobile experience
    decodeBtn.addEventListener('click', async () => {
        if (!decodeImageElement) {
            updateStatus('Please select an image to decode');
            return;
        }
        
        try {
            showLoading('Decoding data from image... This might take a moment.');
            updateStatus('Decoding data...');
            
            const decodedData = await decodeDataFromImage(decodeImageElement);
            const processedData = processDecodedData(decodedData);
            
            hideLoading();
            
            if (processedData.type === 'text') {
                // Display text
                openModal('Decoded Message', `
                    <p>The following message was decoded from the image:</p>
                    <pre>${escapeHtml(processedData.content)}</pre>
                `);
                updateStatus('Message decoded successfully');
                
            } else if (processedData.type === 'file') {
                // Prepare file download
                openModal('Decoded File', `
                    <p>A file was decoded from the image with extension: <strong>.${processedData.extension}</strong></p>
                    <p>Size: ${(processedData.content.length/1024).toFixed(1)} KB</p>
                    <button id="download-decoded-file" class="primary-btn" style="margin: 15px 0;">Download Decoded File</button>
                `);
                
                // Add event listener to the download button
                document.getElementById('download-decoded-file').addEventListener('click', () => {
                    if (isIOS()) {
                        alert("iOS Safari doesn't support file downloads. We'll try to open it directly if possible, but some file types may not work.");
                    }
                    downloadDecodedFile(processedData.content, processedData.extension);
                    updateStatus('Decoded file downloaded');
                });
                
            } else {
                // Binary data (unknown type)
                openModal('Decoded Data', `
                    <p>Unrecognized data format was found in the image.</p>
                    <p>Size: ${(processedData.content.length/1024).toFixed(1)} KB</p>
                    <button id="download-binary-data" class="primary-btn" style="margin: 15px 0;">Download Raw Data</button>
                `);
                
                // Add event listener to the download button
                document.getElementById('download-binary-data').addEventListener('click', () => {
                    if (isIOS()) {
                        alert("iOS Safari doesn't support file downloads. We'll try to open it directly if possible.");
                    }
                    downloadDecodedFile(processedData.content, 'bin');
                    updateStatus('Raw data downloaded');
                });
            }
            
        } catch (error) {
            hideLoading();
            updateStatus(`Error: ${error.message}`);
            alert(`Decoding failed: ${error.message}`);
        }
    });
    
    // Improved modal handling for mobile
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside of it or pressing escape
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
    
    // Handle device orientation changes
    window.addEventListener('resize', () => {
        isMobile = window.matchMedia("(max-width: 768px)").matches;
    });
    
    // Helper functions
    function openModal(title, content) {
        modalTitle.textContent = title;
        modalBody.innerHTML = content;
        modal.style.display = 'block';
        
        // Prevent body scrolling when modal is open
        document.body.style.overflow = 'hidden';
        
        // When modal closes, restore scrolling
        const closeFunction = () => {
            document.body.style.overflow = '';
            modal.removeEventListener('transitionend', closeFunction);
        };
        modal.addEventListener('transitionend', closeFunction);
    }
    
    function updateStatus(message) {
        statusText.textContent = message;
    }
    
    function showLoading(message) {
        loadingText.textContent = message || 'Processing...';
        loadingOverlay.classList.remove('hidden');
        // Prevent scrolling during loading
        document.body.style.overflow = 'hidden';
    }
    
    function hideLoading() {
        loadingOverlay.classList.add('hidden');
        // Restore scrolling
        document.body.style.overflow = '';
    }
    
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/<//g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Detect iOS for special file handling
    function isIOS() {
        return [
            'iPad Simulator',
            'iPhone Simulator',
            'iPod Simulator',
            'iPad',
            'iPhone',
            'iPod'
        ].includes(navigator.platform)
        // iPad on iOS 13 detection
        || (navigator.userAgent.includes("Mac") && "ontouchend" in document);
    }
    
    // Initialize the app
    updateStatus('Ready');
});