/**
 * Steganography Web Application
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
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(`${button.dataset.tab}-tab`).classList.add('active');
        });
    });
    
    // File input handlers
    document.querySelectorAll('.file-input').forEach(container => {
        const input = container.querySelector('input[type="file"]');
        const button = container.querySelector('.browse-btn');
        
        button.addEventListener('click', () => {
            input.click();
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
    
    // Handle encode image selection
    encodeImageInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            const file = event.target.files[0];
            
            if (file.type !== 'image/png') {
                updateStatus('Error: Only PNG images are supported');
                return;
            }
            
            encodeImageName.textContent = file.name;
            updatePreview(file, encodePreviewImage, encodePreviewPlaceholder);
            
            // Create Image element for encoding
            const reader = new FileReader();
            reader.onload = (e) => {
                encodeImageElement = new Image();
                encodeImageElement.onload = () => {
                    const maxBytes = Math.floor((encodeImageElement.width * encodeImageElement.height * 3 * BITS_PER_CHANNEL) / 8);
                    imageInfo.textContent = `Size: ${encodeImageElement.width}x${encodeImageElement.height} pixels | Max capacity: ${(maxBytes/1024).toFixed(1)} KB`;
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
            encodeFileName.textContent = selectedFile.name;
            
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
            
            fileInfo.textContent = `File: ${selectedFile.name} | Type: ${extension.toUpperCase()} | Size: ${sizeText}`;
            
            // Warn if file is too large
            if (selectedFile.size > 5 * 1024 * 1024) {
                fileInfo.textContent += ' (Large file - encoding may be slow)';
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
            
            decodeImageName.textContent = file.name;
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
    
    // Update image preview
    function updatePreview(file, imgElement, placeholder) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imgElement.src = e.target.result;
            imgElement.classList.remove('hidden');
            placeholder.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    }
    
    // Encode button
    encodeBtn.addEventListener('click', async () => {
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
                if (selectedFile.size > maxBytes * 0.7) { 
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
            
            const url = URL.createObjectURL(encodedImageBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'encoded_' + (encodeImageName.textContent || 'image.png');
            
            hideLoading();
            
            openModal('Encoding Successful', `
                <p>Your data has been successfully encoded into the image!</p>
                <p>Click the button below to download the encoded image:</p>
                <button id="download-encoded-image" class="primary-btn" style="margin: 15px 0;">Download Encoded Image</button>
            `);
            
            document.getElementById('download-encoded-image').addEventListener('click', () => {
                a.click();
                updateStatus('Encoded image downloaded');
            });
            
            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 60000);
            
        } catch (error) {
            hideLoading();
            updateStatus(`Error: ${error.message}`);
            alert(`Encoding failed: ${error.message}`);
        }
    });
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
                openModal('Decoded Message', `
                    <p>The following message was decoded from the image:</p>
                    <pre>${escapeHtml(processedData.content)}</pre>
                `);
                updateStatus('Message decoded successfully');
                
            } else if (processedData.type === 'file') {
                openModal('Decoded File', `
                    <p>A file was decoded from the image with extension: <strong>.${processedData.extension}</strong></p>
                    <p>Size: ${(processedData.content.length/1024).toFixed(1)} KB</p>
                    <button id="download-decoded-file" class="primary-btn" style="margin: 15px 0;">Download Decoded File</button>
                `);
                
                document.getElementById('download-decoded-file').addEventListener('click', () => {
                    downloadDecodedFile(processedData.content, processedData.extension);
                    updateStatus('Decoded file downloaded');
                });
                
            } else {
                openModal('Decoded Data', `
                    <p>Unrecognized data format was found in the image.</p>
                    <p>Size: ${(processedData.content.length/1024).toFixed(1)} KB</p>
                    <button id="download-binary-data" class="primary-btn" style="margin: 15px 0;">Download Raw Data</button>
                `);
                
                document.getElementById('download-binary-data').addEventListener('click', () => {
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
    
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    function openModal(title, content) {
        modalTitle.textContent = title;
        modalBody.innerHTML = content;
        modal.style.display = 'block';
    }
    
    function updateStatus(message) {
        statusText.textContent = message;
    }
    
    function showLoading(message) {
        loadingText.textContent = message || 'Processing...';
        loadingOverlay.classList.remove('hidden');
    }
    
    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }
    
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    updateStatus('Ready');
});