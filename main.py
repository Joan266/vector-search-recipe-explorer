from pipeline.extract import fetch_mealdb
from pipeline.load import save_to_csv
from pipeline.analyze_health import HealthAnalyzer
from pipeline.analyze_time import TimeAnalyzer
from pipeline.audio_generator import AudioGenerator
from pipeline.embedding_generator import EmbeddingGenerator
from pipeline.mongodb_upload import MongoDBUploader  

def main():
    try:
        print("Starting recipe pipeline...")
        
        # 1. Fetch recipes
        recipes = fetch_mealdb(limit=400)
        
        # 2. Analyze health
        health_analyzer = HealthAnalyzer()
        recipes = health_analyzer.analyze_recipes(recipes)
        
        # 3. Analyze time
        time_analyzer = TimeAnalyzer()
        recipes = time_analyzer.analyze_recipes(recipes)
        
        # 4. Generate audio instructions
        audio_generator = AudioGenerator()
        recipes = audio_generator.process_recipes(recipes)
        
        # 5. Generate embeddings
        embedding_generator = EmbeddingGenerator()
        recipes = embedding_generator.generate_embeddings(recipes)
        
        # 6. Save to CSV
        save_to_csv(recipes)
        
        # 7. Upload to MongoDB (NEW STEP)
        print("\n📦 Uploading to MongoDB...")
        mongo_uploader = MongoDBUploader()
        upload_result = mongo_uploader.upload_recipes(recipes)
        
        if upload_result["success"]:
            print(f"✅ Successfully uploaded {upload_result['inserted_count']} recipes to MongoDB")
        else:
            print(f"❌ MongoDB upload failed: {upload_result['error']}")
            raise Exception(f"MongoDB upload failed: {upload_result['error']}")
        
        print("Pipeline completed successfully!")
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")

if __name__ == "__main__":
    main()