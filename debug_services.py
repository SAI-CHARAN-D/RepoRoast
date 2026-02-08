
import os
from dotenv import load_dotenv
load_dotenv()

from app.services.ai_service import AIService
from app.services.tts_service import TTSService

def test_tts():
    print("Testing TTS Service...")
    tts = TTSService()
    try:
        dialogue = [{"speaker": "Host", "text": "Testing audio generation."}]
        path = tts.generate_roast_audio(dialogue, "debug_test")
        print(f"TTS Output Path: {path}")
    except Exception as e:
        print(f"TTS Failed: {e}")

def test_ai():
    print("\nTesting AI Service...")
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not found in env.")
        return

    ai = AIService()
    try:
        # Simple test 
        print(f"Using model: {ai.model._model_name}")
        response = ai.model.generate_content("Hello")
        print("AI Output:", response.text)
    except Exception as e:
        print(f"AI Failed: {e}")

if __name__ == "__main__":
    test_tts()
    test_ai()
