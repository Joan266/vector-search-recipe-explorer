import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import RecipeCard from '../components/RecipeCard';

export default function Home() {
  const [recipes, setRecipes] = useState([]);
  
  // Mock API call (replace with real fetch later)
  const handleSearch = async (query) => {
    // TEMP: Hardcoded 5 results for demo
    const mockRecipes = [
      {
        idMeal: "52820",
        strMeal: "Katsu Chicken curry",
        strMealThumb: "https://www.themealdb.com/images/media/meals/vwrpps1503068729.jpg",
        strCategory: "Japanese"
      },
      // Add 4 more mock recipes here...
    ];
    setRecipes(mockRecipes);
  };

  return (
    <div className="container">
      <h1>Recipe Finder</h1>
      <SearchBar onSearch={handleSearch} />
      
      <div className="recipe-grid">
        {recipes.map(recipe => (
          <RecipeCard key={recipe.idMeal} recipe={recipe} />
        ))}
      </div>
    </div>
  );
}