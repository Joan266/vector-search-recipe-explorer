from pipeline.extract import fetch_mealdb
from pipeline.load import save_to_csv
from pipeline.analyze_health import HealthAnalyzer
from pipeline.analyze_time import TimeAnalyzer
from pipeline.audio_generator import AudioGenerator

def main():
    try:
        print("Starting recipe pipeline...")
        
        # 1. Fetch recipes
        recipes = fetch_mealdb(limit=2)
        
        # 2. Analyze health
        health_analyzer = HealthAnalyzer()
        recipes = health_analyzer.analyze_recipes(recipes)
        
        # 3. Analyze time
        time_analyzer = TimeAnalyzer()
        recipes = time_analyzer.analyze_recipes(recipes)
        # 4. Generate audio instructions
        audio_generator = AudioGenerator()
        recipes = audio_generator.process_recipes(recipes)
        
        # 5. Save to CSV
        save_to_csv(recipes)
        
        print("Pipeline completed successfully!")
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")

if __name__ == "__main__":
    main()