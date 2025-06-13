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
            name: "Green Power Smoothie",
            image: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80",
            ingredients: ["spinach", "banana", "almond milk", "chia seeds", "peanut butter"],
            prepTime: "5 mins",
            cookTime: "0 mins",
            instructions: "1. Combine all ingredients in blender. 2. Blend until smooth. 3. Pour into glass and enjoy immediately.",
            nutritionScore: 95,
            healthClass: "healthy"
        },
        {
            id: 2,
            name: "Avocado Toast",
            image: "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80",
            ingredients: ["whole grain bread", "avocado", "cherry tomatoes", "feta cheese", "olive oil"],
            prepTime: "10 mins",
            cookTime: "5 mins",
            instructions: "1. Toast bread. 2. Mash avocado with salt and pepper. 3. Spread on toast. 4. Top with tomatoes and feta. 5. Drizzle with olive oil.",
            nutritionScore: 88,
            healthClass: "healthy"
        },
        {
            id: 3,
            name: "Quinoa Salad",
            image: "https://images.unsplash.com/photo-1546069901-6586ba033cce?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80",
            ingredients: ["quinoa", "cucumber", "cherry tomatoes", "red onion", "feta cheese", "lemon juice"],
            prepTime: "15 mins",
            cookTime: "15 mins",
            instructions: "1. Cook quinoa according to package. 2. Chop vegetables. 3. Combine all ingredients in bowl. 4. Dress with lemon juice and olive oil. 5. Chill before serving.",
            nutritionScore: 90,
            healthClass: "healthy"
        }
    ];

    // Search function
    searchBtn.addEventListener('click', async function() {
        const ingredients = ingredientInput.value.trim();
        if (!ingredients) return;
        
        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        resultsContainer.innerHTML = '';
        healthMeter.classList.add('hidden');
        audioPlayer.classList.add('hidden');
        
        try {
            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 1800));
            
            // In a real app, you would call your backend API here:
            // const response = await fetch(`/api/recipes/search?ingredients=${encodeURIComponent(ingredients)}`);
            // const recipes = await response.json();
            
            // Display results
            displayRecipes(mockRecipes);
            
            // Update health meter with first recipe's score
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
        
        recipes.forEach((recipe, index) => {
            const recipeCard = document.createElement('div');
            recipeCard.className = 'recipe-card fade-in';
            recipeCard.style.animationDelay = `${index * 0.2}s`;
            
            recipeCard.innerHTML = `
                <img src="${recipe.image}" alt="${recipe.name}" class="recipe-bg">
                <div class="recipe-content">
                    <h3 class="recipe-title">${recipe.name}</h3>
                    <div class="recipe-meta">
                        <span><i class="fas fa-clock"></i> ${recipe.prepTime} prep</span>
                        <span><i class="fas fa-fire"></i> ${recipe.cookTime} cook</span>
                        <span class="${recipe.healthClass}"><i class="fas fa-apple-alt"></i> ${recipe.nutritionScore}%</span>
                    </div>
                    <h4><i class="fas fa-carrot"></i> Ingredients:</h4>
                    <ul class="ingredients-list">
                        ${recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')}
                    </ul>
                    <button class="audio-btn" data-id="${recipe.id}">
                        <i class="fas fa-play-circle"></i> Listen to Instructions
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
        
        // Set feedback based on score
        if (score > 85) {
            healthFeedback.innerHTML = `<span class="healthy">Excellent choice! This recipe is packed with nutrients and low in processed ingredients.</span>`;
        } else if (score > 70) {
            healthFeedback.innerHTML = `<span class="moderate">Good option! This recipe offers balanced nutrition and wholesome ingredients.</span>`;
        } else if (score > 50) {
            healthFeedback.innerHTML = `<span class="moderate">Moderate nutrition. Contains some less healthy ingredients - enjoy in moderation.</span>`;
        } else {
            healthFeedback.innerHTML = `<span class="unhealthy">Less healthy. High in processed ingredients - consider as an occasional treat.</span>`;
        }
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