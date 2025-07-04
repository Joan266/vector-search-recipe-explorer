// Audio Guide Functionality
document.addEventListener('DOMContentLoaded', function() {
    const audioGuide = document.getElementById('audio-guide');
    if (!audioGuide) return;

    const audioPlayer = new Audio();
    let currentStepIndex = 0;
    const steps = Array.from(document.querySelectorAll('.audio-step'));
    
    // Control buttons
    const playPauseBtn = document.getElementById('play-pause');
    const prevBtn = document.getElementById('prev-step');
    const nextBtn = document.getElementById('next-step');

    // Highlight current step
    function highlightStep(index) {
        steps.forEach((step, i) => {
            step.classList.toggle('active', i === index);
            
            // Scroll to step if it's not fully visible
            if (i === index) {
                step.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    }

    // Play audio for current step
    function playCurrentStep() {
        const step = steps[currentStepIndex];
        if (!step) return;
        
        const audioUrl = step.dataset.audioUrl;
        if (!audioUrl) return;
        
        audioPlayer.src = audioUrl;
        audioPlayer.play().catch(e => console.error("Audio playback failed:", e));
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="bi bi-pause-fill"></i>';
        }
        highlightStep(currentStepIndex);
    }

    // Event listeners
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', function() {
            if (audioPlayer.paused) {
                playCurrentStep();
            } else {
                audioPlayer.pause();
                playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentStepIndex > 0) {
                currentStepIndex--;
                playCurrentStep();
                if (nextBtn) nextBtn.disabled = false;
            }
            if (prevBtn) prevBtn.disabled = currentStepIndex <= 0;
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentStepIndex < steps.length - 1) {
                currentStepIndex++;
                playCurrentStep();
                if (prevBtn) prevBtn.disabled = false;
            }
            if (nextBtn) nextBtn.disabled = currentStepIndex >= steps.length - 1;
        });
    }

    // Click on step to play
    steps.forEach(step => {
        step.addEventListener('click', function() {
            currentStepIndex = parseInt(this.dataset.step) || 0;
            playCurrentStep();
            if (prevBtn) prevBtn.disabled = currentStepIndex <= 0;
            if (nextBtn) nextBtn.disabled = currentStepIndex >= steps.length - 1;
        });
    });

    // Audio player events
    audioPlayer.addEventListener('play', function() {
        if (playPauseBtn) playPauseBtn.innerHTML = '<i class="bi bi-pause-fill"></i>';
    });

    audioPlayer.addEventListener('pause', function() {
        if (playPauseBtn) playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
    });

    audioPlayer.addEventListener('ended', function() {
        if (currentStepIndex < steps.length - 1) {
            currentStepIndex++;
            playCurrentStep();
            if (prevBtn) prevBtn.disabled = false;
        } else {
            if (playPauseBtn) playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
        }
        if (nextBtn) nextBtn.disabled = currentStepIndex >= steps.length - 1;
    });

    // Initialize
    highlightStep(0);
    if (prevBtn) prevBtn.disabled = true;
});

// Search Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Helper functions
    const preventDefaults = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const highlight = () => {
        const dropArea = document.getElementById('drop-area');
        if (dropArea) dropArea.classList.add('highlight');
    };

    const unhighlight = () => {
        const dropArea = document.getElementById('drop-area');
        if (dropArea) dropArea.classList.remove('highlight');
    };

    const handleFiles = (e) => {
        const dropArea = document.getElementById('drop-area');
        const fileInput = document.getElementById('file-input');
        const uploadedImage = document.getElementById('uploaded-image');
        const imagePreview = document.getElementById('image-preview');
        
        if (!fileInput || !dropArea || !uploadedImage || !imagePreview) return;

        const files = e.target.files;
        if (!files.length) return;

        const file = files[0];
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            currentImage = event.target.result;
            uploadedImage.src = currentImage;
            imagePreview.style.display = 'flex';
            dropArea.classList.add('has-image');
            updateSearchButtonState();
        };
        reader.readAsDataURL(file);
    };

    const handleDrop = (e) => {
        const dt = e.dataTransfer;
        handleFiles({ target: { files: dt.files } });
    };

    const clearImage = (e) => {
        if (e) e.stopPropagation();
        const fileInput = document.getElementById('file-input');
        const uploadedImage = document.getElementById('uploaded-image');
        const imagePreview = document.getElementById('image-preview');
        const dropArea = document.getElementById('drop-area');
        
        if (!fileInput || !uploadedImage || !imagePreview || !dropArea) return;
        
        currentImage = null;
        fileInput.value = '';
        uploadedImage.src = '#';
        imagePreview.style.display = 'none';
        dropArea.classList.remove('has-image');
        updateSearchButtonState();
    };

    const displaySearchResults = (results) => {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;
        
        searchResults.innerHTML = results.length ? '' : `
            <div class="col-12">
                <div class="alert alert-info">
                    No recipes found. Try a different search term or image.
                </div>
            </div>`;

        results.forEach(recipe => {
            const col = document.createElement('div');
            col.className = 'col-md-4 mb-4';
            col.innerHTML = `
                <div class="card h-100">
                    <img src="${recipe.img_url}" class="card-img-top" alt="${recipe.name}">
                    <div class="card-body">
                        <h5 class="card-title">${recipe.name}</h5>
                        <p class="card-text">
                            <span class="badge bg-primary">${recipe.category}</span>
                            <span class="badge bg-secondary">${recipe.area}</span>
                            ${recipe.score ? `<span class="badge bg-success">Score: ${recipe.score.toFixed(2)}</span>` : ''}
                        </p>
                        <a href="/recipe/${recipe._id}" class="btn btn-primary">View Recipe</a>
                    </div>
                </div>
            `;
            searchResults.appendChild(col);
        });
    };

    const updateSearchButtonState = () => {
        const searchButton = document.getElementById('search-button') || 
                           document.querySelector('.search-form button[type="submit"]');
        const searchInput = document.getElementById('search-input');
        
        if (!searchButton || !searchInput) return;
        
        const hasQuery = searchInput.value.trim();
        const hasImage = currentImage;
        
        searchButton.disabled = !(hasQuery || hasImage);
        searchButton.title = hasImage ? 
            "Search with uploaded image" : 
            (hasQuery ? "Search with text" : "Enter text or upload image to search");
    };

    // Main search handler
    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        
        const searchButton = document.getElementById('search-button') || 
                           document.querySelector('.search-form button[type="submit"]');
        const searchResults = document.getElementById('search-results');
        const searchInput = document.getElementById('search-input');
        
        if (!searchButton || !searchResults || !searchInput || isSearching) return;

        const query = searchInput.value.trim();
        if (!query && !currentImage) {
            alert('Please enter a search term or upload an image');
            return;
        }

        // Set loading state
        isSearching = true;
        searchButton.classList.add('btn-loading');
        searchButton.disabled = true;
        searchResults.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"></div></div>';

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, image: currentImage })
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: 'Search failed' }));
                throw new Error(error.error || 'Search failed');
            }

            const data = await response.json();
            displaySearchResults(data);
        } catch (error) {
            console.error('Search Error:', error);
            searchResults.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        ${error.message || 'Search failed. Please try again.'}
                    </div>
                </div>`;
        } finally {
            isSearching = false;
            searchButton.classList.remove('btn-loading');
            updateSearchButtonState();
        }
    };

    // State
    let currentImage = null;
    let isSearching = false;

    // Initialize search functionality only if elements exist
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const searchButton = document.getElementById('search-button') || searchForm?.querySelector('button[type="submit"]');
    
    if (!searchForm || !searchInput || !searchResults || !searchButton) {
        return;
    }

    // Initialize drop area if exists
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const imagePreview = document.getElementById('image-preview');
    const uploadedImage = document.getElementById('uploaded-image');
    const clearImageBtn = document.getElementById('clear-image');

    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight);
        });

        dropArea.addEventListener('drop', handleDrop);
        dropArea.addEventListener('click', () => fileInput?.click());
    }

    if (fileInput) fileInput.addEventListener('change', handleFiles);
    if (clearImageBtn) clearImageBtn.addEventListener('click', clearImage);
    if (searchForm) searchForm.addEventListener('submit', handleSearch);
    if (searchInput) searchInput.addEventListener('input', updateSearchButtonState);

    // Initial setup
    updateSearchButtonState();
});
