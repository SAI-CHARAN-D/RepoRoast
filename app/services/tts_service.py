

import os
import json
import tempfile
from app.services.guardrail_service import ensure_cache_dir

# Ensure generated directory exists for frontend serving
GENERATED_DIR = os.path.join(os.getcwd(), 'app', 'static', 'generated')

def ensure_generated_dir():
    if not os.path.exists(GENERATED_DIR):
        os.makedirs(GENERATED_DIR)

class TTSService:
    def __init__(self):
        self.use_google_cloud = False
        self.client = None
        self.credentials = None
        self.voice_roaster = None
        self.voice_explainer = None
        self.audio_config = None
        self._initialized = False

    def _initialize_client(self):
        """Lazy load Google Cloud TTS client"""
        if self._initialized:
            return

        from google.cloud import texttospeech
        from google.oauth2 import service_account

        try:
            # Option 1: Load from GOOGLE_CLOUD_TTS_JSON env variable (JSON content)
            tts_json = os.getenv('GOOGLE_CLOUD_TTS_JSON')
            
            if tts_json and tts_json.strip():
                try:
                    credentials_info = json.loads(tts_json)
                    self.credentials = service_account.Credentials.from_service_account_info(credentials_info)
                    print("✅ TTS: Loaded credentials from GOOGLE_CLOUD_TTS_JSON")
                except json.JSONDecodeError as je:
                    print(f"❌ TTS: GOOGLE_CLOUD_TTS_JSON is not valid JSON: {je}")
            
            # Option 2: Load from GOOGLE_APPLICATION_CREDENTIALS env variable (file path)
            if not self.credentials:
                creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if creds_path and os.path.exists(creds_path):
                    self.credentials = service_account.Credentials.from_service_account_file(creds_path)
                    print(f"✅ TTS: Loaded credentials from {creds_path}")
            
            # Initialize client with credentials
            if self.credentials:
                self.client = texttospeech.TextToSpeechClient(credentials=self.credentials)
                print("✅ TTS: TextToSpeechClient initialized with credentials")
            else:
                try:
                    # Try default credentials (for Google Cloud environments)
                    self.client = texttospeech.TextToSpeechClient()
                    print("TTS DEBUG: Using default credentials")
                except Exception:
                     # If even default fails, we can't use Cloud TTS
                     pass

            if self.client:
                self.use_google_cloud = True
                
                # Voice Configuration (Cloud)
                self.voice_roaster = texttospeech.VoiceSelectionParams(
                    language_code="en-US", name="en-US-Studio-M"
                )
                self.voice_explainer = texttospeech.VoiceSelectionParams(
                    language_code="en-US", name="en-US-Studio-O" 
                )
                self.audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.1
                )
                print("🎉 TTS: Google Cloud Client initialized successfully.")
            
        except Exception as e:
            print(f"❌ TTS: Initialization failed ({e}). Falling back to gTTS.")
            self.use_google_cloud = False
            
        self._initialized = True

    def format_text_to_ssml(self, text, speaker):
        """
        Wraps plain text in SSML tags for better prosody.
        Studio voices don't support pitch, so we only use rate.
        """
        # Determine rate based on speaker
        if speaker in ["Host", "Roaster"]:
            # Roaster: Slightly faster for energetic delivery
            rate = "105%"
        else:
            # Explainer: Slightly slower for calm, clear delivery
            rate = "95%"
        
        # Wrap in SSML speak tags with prosody (rate only, no pitch for Studio voices)
        ssml = f'<speak><prosody rate="{rate}">{text}</prosody></speak>'
        
        return ssml

    def synthesize_turn_cloud(self, text, speaker):
        """Synthesizes using Google Cloud TTS with SSML."""
        self._initialize_client()
        if not self.client: return None

        from google.cloud import texttospeech # Lazy import

        voice = self.voice_roaster if speaker in ["Host", "Roaster"] else self.voice_explainer
        
        # Format text as SSML
        ssml_text = self.format_text_to_ssml(text, speaker)
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        
        try:
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=self.audio_config
            )
            return response.audio_content
        except Exception as e:
            print(f"Cloud TTS failed: {e}")
            return None

    def synthesize_turn_gtts(self, text, speaker):
        """Synthesizes using gTTS (Google Translate unofficial API)."""
        from gtts import gTTS
        try:
            # gTTS doesn't support many voices, so we vary by tld or speed slightly?
            # Actually gTTS is limited. We'll just use standard English.
            # Maybe use 'co.uk' for one speaker to differentiate.
            tld = 'us' if speaker in ["Host", "Roaster"] else 'co.uk'
            tts = gTTS(text=text, lang='en', tld=tld, slow=False)
            
            # gTTS saves to file, so we need to read it back into bytes
            # efficient way using io.BytesIO
            import io
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
        except Exception as e:
            print(f"gTTS failed: {e}")
            return None

    def generate_silence(self, duration_ms=300):
        """
        Generates a silent audio segment using SSML break.
        Duration in milliseconds.
        """
        self._initialize_client()

        if not self.use_google_cloud or not self.client:
            return b""  # gTTS doesn't support SSML breaks easily
        
        from google.cloud import texttospeech # Lazy import

        ssml = f'<speak><break time="{duration_ms}ms"/></speak>'
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        
        try:
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice_roaster,  # voice doesn't matter for silence
                audio_config=self.audio_config
            )
            return response.audio_content
        except Exception as e:
            print(f"Silence generation failed: {e}")
            return b""

    def generate_roast_audio(self, dialogue_list, unique_id):
        """
        Generates full conversation audio and saves to static/generated.
        """
        if not dialogue_list:
            return None
            
        ensure_generated_dir()
        
        # Initialize client to determine if we can use Cloud TTS
        self._initialize_client()
        
        output_filename = f"roast_{unique_id}.mp3"
        output_path = os.path.join(GENERATED_DIR, output_filename)
        
        # CACHING DISABLED: Always generate fresh audio
        # if os.path.exists(output_path):
        #     return f"generated/{output_filename}"

        combined_audio = b""
        print(f"Synthesizing {len(dialogue_list)} turns using {'Google Cloud' if self.use_google_cloud else 'gTTS'}...")
        
        for i, turn in enumerate(dialogue_list):
            speaker = turn.get('speaker', 'Unknown')
            text = turn.get('text', '')
            if not text: continue
                
            if self.use_google_cloud:
                chunk = self.synthesize_turn_cloud(text, speaker)
            else:
                chunk = self.synthesize_turn_gtts(text, speaker)
                
            if chunk:
                combined_audio += chunk
                
                # Add pause between turns (not after last turn)
                if i < len(dialogue_list) - 1 and self.use_google_cloud:
                    pause = self.generate_silence(duration_ms=1000)
                    if pause:
                        combined_audio += pause

        if not combined_audio:
            return None

        with open(output_path, "wb") as out:
            out.write(combined_audio)
            
        return f"generated/{output_filename}"

if __name__ == "__main__":
    # Test Stub
    service = TTSService()
    if service.available:
        mock_dialogue = [
            {"speaker": "Roaster", "text": "This code looks like it was written by a caffeinated squirrel."},
            {"speaker": "Explainer", "text": "It's actually an advanced distributed system pattern, just... misunderstood."}
        ]
        result = service.generate_roast_audio(mock_dialogue, "test_run")
        print("Audio saved to:", result)
    else:
        print("Service unavailable (no creds).")
