from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from .audio.text_processor import TextProcessor
from .audio.analyzer import InstructionAnalyzer
from .audio.speech_synthesizer import SpeechSynthesizer

class AudioGenerator:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.analyzer = InstructionAnalyzer()
        self.synthesizer = SpeechSynthesizer()

    def process_recipe(self, recipe: Dict) -> Optional[Dict]:
        """Process a single recipe to generate audio instructions"""
        if not recipe.get("instructions"):
            return None
            
        try:
            # Transform and normalize instructions
            transformed = self.text_processor.transform_instructions(recipe["instructions"])
            normalized = self.text_processor.normalize_text(transformed)
            steps = self.text_processor.split_into_steps(normalized)
            
            audio_steps = []
            for i, step in enumerate(steps):
                analysis = self.analyzer.analyze(step)  # Used internally for SSML
                audio_url = self.synthesizer.generate_audio(step, recipe['meal_id'], i, analysis)
                if audio_url:
                    audio_steps.append({
                        "step_number": i,
                        "text": step,
                        "audio_url": audio_url  
                    })
            
            return {**recipe, "audio_steps": audio_steps} if audio_steps else None
            
        except Exception as e:
            logging.error(f"Failed to process recipe {recipe.get('meal_id')}: {str(e)}")
            return None

    def process_recipes(self, recipes: List[Dict]) -> List[Dict]:
        """Process multiple recipes in parallel with thread pooling"""
        results = []
        
        # Optimal workers: min(32, os.cpu_count() + 4) for I/O-bound tasks
        with ThreadPoolExecutor(max_workers=10) as executor:  
            future_to_recipe = {
                executor.submit(self.process_recipe, recipe): recipe 
                for recipe in recipes
            }
            
            for future in as_completed(future_to_recipe):
                try:
                    if processed := future.result():
                        results.append(processed)
                except Exception as e:
                    logging.error(f"Thread error: {str(e)}")
        
        return results