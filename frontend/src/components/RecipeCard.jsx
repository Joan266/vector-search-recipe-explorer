export default function RecipeCard({ recipe }) {
  return (
    <div className="card">
      <img src={recipe.strMealThumb} alt={recipe.strMeal} />
      <div className="card-body">
        <h3>{recipe.strMeal}</h3>
        <p>{recipe.strCategory}</p>
        <a href={`/recipe/${recipe.idMeal}`}>View Details</a>
      </div>
    </div>
  );
}