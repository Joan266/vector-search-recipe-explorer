document.addEventListener('DOMContentLoaded', function() {
    const ingredientInput = document.getElementById('ingredient-input');
    const searchBtn = document.getElementById('search-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const imagePreview = document.getElementById('image-preview');
    const resultsContainer = document.getElementById('results');
    const audioPlayer = document.getElementById('audio-player');
    const loadingIndicator = document.getElementById('loading');
    
    let uploadedImage = null;

    // Handle image upload
    uploadBtn.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                uploadedImage = event.target.result;
                imagePreview.innerHTML = `<img src="${uploadedImage}" alt="Uploaded preview" class="uploaded-image">`;
                imagePreview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    });

    // Clear uploaded image
    document.getElementById('clear-image').addEventListener('click', function() {
        uploadedImage = null;
        imagePreview.innerHTML = '';
        imagePreview.classList.add('hidden');
        document.getElementById('upload-btn').value = '';
    });

    // Search function
    searchBtn.addEventListener('click', async function() {
        const ingredients = ingredientInput.value.trim();
        if (!ingredients && !uploadedImage) {
            alert('Please enter ingredients or upload an image');
            return;
        }
        
        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        resultsContainer.innerHTML = '';
        audioPlayer.classList.add('hidden');
        
        try {
            const response = await fetch('/api/recipes/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ingredients: ingredients,
                    image: uploadedImage
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch recipes');
            }
            
            const recipes = await response.json();
            
            // Display results
            displayRecipes(recipes);
            
        
        } catch (error) {
            console.error('Error fetching recipes:', error);
            resultsContainer.innerHTML = '<p class="error">Failed to load recipes. Please try again.</p>';
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    // Display recipes
    function displayRecipes(recipes) {
        resultsContainer.innerHTML = '';
        
        recipes.forEach((recipe, index) => {
            const recipeCard = document.createElement('div');
            recipeCard.className = 'recipe-card fade-in';
            recipeCard.style.animationDelay = `${index * 0.2}s`;
            
            recipeCard.innerHTML = `
                <div class="recipe-image-container">
                    <img src="${recipe.image}" alt="${recipe.name}" class="recipe-image">
                </div>
                
                <div class="recipe-meta">
                    ${recipe.category ? `<span class="meta-category"><i class="fas fa-tag"></i> ${recipe.category}</span>` : ''}
                    ${recipe.area ? `<span class="meta-area"><i class="fas fa-globe"></i> ${recipe.area}</span>` : ''}
                    ${recipe.score ? `<span class="meta-score"><i class="fas fa-star"></i> ${recipe.score.toFixed(2)}</span>` : ''}
                </div>
                
                <div class="recipe-bottom-container">
                    <h3 class="recipe-title">${recipe.name}</h3>
                    <p class="ingredient-count">${recipe.ingredients.length} ingredients</p>
                    <button class="cta-button">
                        View Recipe <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            `;
            
            // Add click event to the entire card
            recipeCard.addEventListener('click', function(e) {
                // Don't navigate if click was on the CTA button (let button handle it)
                if (!e.target.closest('.cta-button')) {
                    window.location.href = `/recipe/${recipe.id}`;
                }
            });
            
            // Add click event to the CTA button specifically
            const ctaButton = recipeCard.querySelector('.cta-button');
            if (ctaButton) {
                ctaButton.addEventListener('click', function(e) {
                    e.stopPropagation(); // Prevent the card click from also firing
                    window.location.href = `/recipe/${recipe.id}`;
                });
            }
            
            resultsContainer.appendChild(recipeCard);
        });

        // Keep your existing audio button listeners if needed
        document.querySelectorAll('.audio-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const recipeId = this.getAttribute('data-id');
                playInstructions(recipeId);
            });
        });
    }

    // Play instructions audio
    async function playInstructions(recipeId) {
        try {
            // Get recipe data
            const recipe = mockRecipes.find(r => r.id == recipeId);
            if (!recipe) return;
            
            // Hide any previous audio player
            audioPlayer.classList.add('hidden');
            
            // For demo, we'll use text-to-speech in the browser
            if ('speechSynthesis' in window) {
                // Stop any current speech
                window.speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(recipe.instructions);
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                utterance.volume = 1;
                
                // Show audio player UI
                audioPlayer.classList.remove('hidden');
                
                // Speak the instructions
                window.speechSynthesis.speak(utterance);
                
                // Update button text during playback
                const button = document.querySelector(`.audio-btn[data-id="${recipeId}"]`);
                button.innerHTML = '<i class="fas fa-pause-circle"></i> Pause Instructions';
                
                utterance.onend = function() {
                    button.innerHTML = '<i class="fas fa-play-circle"></i> Listen to Instructions';
                };
            } else {
                alert("Audio playback not supported in this browser. Instructions:\n" + recipe.instructions);
            }
        } catch (error) {
            console.error('Error playing instructions:', error);
            alert('Failed to load audio instructions');
        }
    }

    // Initialize with placeholder text
    ingredientInput.value = "avocado, quinoa, spinach";
});
