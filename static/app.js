document.addEventListener('DOMContentLoaded', function() {
    const ingredientInput = document.getElementById('ingredient-input');
    const searchBtn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('results');
    const healthMeter = document.getElementById('health-meter');
    const healthBar = document.getElementById('health-bar');
    const healthScore = document.getElementById('health-score');
    const healthFeedback = document.getElementById('health-feedback');
    const audioPlayer = document.getElementById('audio-player');
    const loadingIndicator = document.getElementById('loading');

    // Sample data - replace with actual API calls
    const mockRecipes = [
        {
            id: 1,
            name: "Vegetable Omelette",
            image: "https://images.unsplash.com/photo-1551183053-bf91a1d81141",
            ingredients: ["eggs", "bell peppers", "onions", "cheese"],
            prepTime: "15 mins",
            instructions: "1. Beat the eggs. 2. Chop vegetables. 3. Cook eggs in pan. 4. Add vegetables and cheese. 5. Fold and serve.",
            nutritionScore: 85
        },
        {
            id: 2,
            name: "Chicken Stir Fry",
            image: "https://images.unsplash.com/photo-1607602132700-0681204ef11a",
            ingredients: ["chicken", "broccoli", "soy sauce", "garlic"],
            prepTime: "25 mins",
            instructions: "1. Cut chicken into strips. 2. Stir-fry vegetables. 3. Add chicken and cook through. 4. Add sauce and serve with rice.",
            nutritionScore: 72
        }
    ];

    // Search function
    searchBtn.addEventListener('click', async function() {
        const ingredients = ingredientInput.value.trim();
        if (!ingredients) return;
        
        loadingIndicator.classList.remove('hidden');
        resultsContainer.innerHTML = '';
        healthMeter.classList.add('hidden');
        audioPlayer.classList.add('hidden');
        
        try {
            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // In a real app, you would call your backend API here:
            // const response = await fetch(`/api/recipes/search?ingredients=${encodeURIComponent(ingredients)}`);
            // const recipes = await response.json();
            
            displayRecipes(mockRecipes);
            updateHealthMeter(mockRecipes[0].nutritionScore);
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
        
        recipes.forEach(recipe => {
            const recipeCard = document.createElement('div');
            recipeCard.className = 'recipe-card';
            
            recipeCard.innerHTML = `
                <img src="${recipe.image}" alt="${recipe.name}" class="recipe-image">
                <div class="recipe-content">
                    <h3 class="recipe-title">${recipe.name}</h3>
                    <div class="recipe-meta">
                        <span><i class="fas fa-clock"></i> ${recipe.prepTime}</span>
                        <span><i class="fas fa-utensils"></i> ${recipe.ingredients.length} ingredients</span>
                    </div>
                    <h4>Ingredients:</h4>
                    <ul class="ingredients-list">
                        ${recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')}
                    </ul>
                    <button class="audio-btn" data-id="${recipe.id}">
                        <i class="fas fa-play"></i> Listen to Instructions
                    </button>
                </div>
            `;
            
            resultsContainer.appendChild(recipeCard);
        });

        // Add event listeners to audio buttons
        document.querySelectorAll('.audio-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const recipeId = this.getAttribute('data-id');
                playInstructions(recipeId);
            });
        });
    }

    // Update health meter
    function updateHealthMeter(score) {
        healthMeter.classList.remove('hidden');
        healthBar.style.width = `${score}%`;
        healthScore.textContent = `${score}%`;
        
        // Set color based on score
        if (score > 75) {
            healthBar.style.backgroundColor = var(--healthy);
            healthFeedback.textContent = "Very healthy! Great choice!";
        } else if (score > 50) {
            healthBar.style.backgroundColor = var(--moderate);
            healthFeedback.textContent = "Moderately healthy. Good option!";
        } else {
            healthBar.style.backgroundColor = var(--unhealthy);
            healthFeedback.textContent = "Less healthy. Enjoy in moderation!";
        }
    }

    // Play instructions audio
    async function playInstructions(recipeId) {
        try {
            // In a real app, you would call your backend API here:
            // const response = await fetch(`/api/recipes/${recipeId}/audio`);
            // const audioBlob = await response.blob();
            // const audioUrl = URL.createObjectURL(audioBlob);
            
            // For demo, we'll use text-to-speech in the browser
            const recipe = mockRecipes.find(r => r.id == recipeId);
            if (!recipe) return;
            
            // Hide any previous audio player
            audioPlayer.classList.add('hidden');
            
            // Use Web Speech API for demo (in production, use Google Cloud Text-to-Speech)
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(recipe.instructions);
                window.speechSynthesis.speak(utterance);
            } else {
                // Fallback - show instructions in console
                console.log("Audio instructions:", recipe.instructions);
                alert("Audio playback not supported in this browser. Instructions:\n" + recipe.instructions);
            }
            
            // In a real implementation with your backend:
            // audioPlayer.src = audioUrl;
            // audioPlayer.classList.remove('hidden');
            // audioPlayer.play();
        } catch (error) {
            console.error('Error playing instructions:', error);
            alert('Failed to load audio instructions');
        }
    }

    // Initialize with some sample data for demo
    if (window.location.href.includes('demo=true')) {
        ingredientInput.value = "eggs, chicken, vegetables";
        searchBtn.click();
    }
});