from flask import Flask, jsonify, send_from_directory
import requests

app = Flask(__name__)

# Serve static files
@app.route('/')
def home():
    return send_from_directory('../static', 'index.html')

# Mock API endpoint
@app.route('/api/recipes')
def get_recipes():
    mock_recipes = [
        {
            "id": "52820",
            "name": "Katsu Chicken Curry",
            "category": "Japanese",
            "img_url": "https://www.themealdb.com/images/media/meals/vwrpps1503068729.jpg",
            "ingredients": "4 chicken breasts, 2 tbsp flour...",
            "youtube_url": "https://www.youtube.com/watch?v=MWzxDFRtVbc"
        },
        # Add 4 more mock recipes here
    ]
    return jsonify(mock_recipes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)