from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS  # Add this
from scripts.mealdb_access_API import fetch_mealdb  # New version

app = Flask(__name__, static_folder='../static')  # Point to static folder
CORS(app)  # Enable CORS

# Serve static files
@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

# API endpoint
@app.route('/api/recipes')
def get_recipes():
    if not hasattr(app, 'cached_recipes'):
        print("Fetching data from TheMealDB...")
        app.cached_recipes = fetch_mealdb(limit=5)
    return jsonify(app.cached_recipes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)