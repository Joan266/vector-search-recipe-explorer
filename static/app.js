async function loadRecipes() {
  const response = await fetch('/api/recipes');
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
}

// Load mock data on startup
loadRecipes();