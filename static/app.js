document.addEventListener('DOMContentLoaded', function() {
    async function loadRecipes() {
        try {
            const response = await fetch('/api/recipes');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const recipes = await response.json();
            
            const container = document.getElementById('results');
            container.innerHTML = recipes.map(recipe => `
                <div class="card">
                    <img src="${recipe.img_url}" alt="${recipe.name}">
                    <h3>${recipe.name}</h3>
                    <p>${recipe.category}</p>
                    <a href="${recipe.youtube_url}" target="_blank">Watch Video</a>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading recipes:', error);
            document.getElementById('results').innerHTML = '<p>Error loading recipes</p>';
        }
    }

    loadRecipes();
});