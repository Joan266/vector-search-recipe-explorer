# Recipe Explorer - Development Setup

A multimodal recipe search application using MongoDB Atlas Vector Search and Google Cloud AI services.

## 🚀 Quick Start

### 1. Environment Setup

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=eco_footprint
COLLECTION_NAME=mealdb_recipes

# Google Cloud Configuration
GCP_PROJECT=your-gcp-project-id
GCP_REGION=us-central1
BUCKET_NAME=recipe-audio-bucket

# API Keys
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Path to Google Cloud service account key file
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Google Cloud Setup

#### Option A: Service Account Key (Recommended for Development)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a service account with the following roles:
   - Vertex AI User
   - Storage Admin
   - Cloud Text-to-Speech Client
   - Cloud Natural Language API Client
3. Download the JSON key file
4. Set the path in your `.env` file: `GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json`

#### Option B: Application Default Credentials
```bash
gcloud auth application-default login
```

### 4. MongoDB Atlas Setup

1. Create a MongoDB Atlas cluster
2. Create vector search indexes for your collection:
   - `recipe_img_vector_index` on `image_embedding` field
   - `recipe_text_vector_index` on `text_embedding` field
3. Add your connection string to `.env`

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🔧 Development Features

- **Hot Reload**: Flask debug mode enabled in development
- **Detailed Logging**: Debug-level logging for troubleshooting
- **Environment Validation**: Clear error messages for missing configuration
- **Pretty JSON**: Formatted JSON responses in development mode

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── templates/           # HTML templates
├── static/             # CSS, JS, and static assets
└── pipeline/           # Data processing scripts
```

## 🛠️ Data Pipeline

The project includes scripts to populate your database with recipe data:

```bash
# Run the complete pipeline
python main.py

# Or run individual components
python pipeline/extract.py
python pipeline/analyze_health.py
python pipeline/analyze_time.py
```

## 🔍 API Endpoints

- `GET /` - Homepage with featured recipes
- `POST /search` - Multimodal recipe search
- `GET /recipe/<id>` - Recipe details page

## 🚨 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check your `MONGODB_URI` in `.env`
   - Ensure your IP is whitelisted in MongoDB Atlas

2. **Vertex AI Initialization Failed**
   - Verify your `GCP_PROJECT` and `GEMINI_API_KEY`
   - Check Google Cloud credentials setup

3. **Missing Environment Variables**
   - Copy `.env.example` to `.env`
   - Fill in all required values

### Debug Mode

Set `FLASK_ENV=development` in your `.env` file to enable:
- Detailed error messages
- Auto-reload on code changes
- Debug logging

## 📚 Additional Resources

- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)