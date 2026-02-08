
import os
import json
import google.generativeai as genai
from app.services.ai_prompts import SYSTEM_PROMPT, generate_user_prompt

class AIService:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # We will handle missing key gracefully later, maybe mock for dev
            print("WARNING: GOOGLE_API_KEY not found in environment variables.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            # User confirmed Gemini 3 Pro Preview
            self.model = genai.GenerativeModel('gemini-3-pro-preview')

    def sanitize_dialogue(self, dialogue_list):
        """
        Removes markdown syntax from dialogue text to prevent TTS from reading it aloud.
        Strips: backticks, asterisks, underscores, brackets
        """
        import re
        for turn in dialogue_list:
            if 'text' in turn:
                text = turn['text']
                # Remove backticks (single and triple)
                text = text.replace('```', '')
                text = text.replace('`', '')
                # Remove bold/italic asterisks and underscores
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
                text = re.sub(r'\*(.+?)\*', r'\1', text)      # *italic*
                text = re.sub(r'__(.+?)__', r'\1', text)      # __bold__
                text = re.sub(r'_(.+?)_', r'\1', text)        # _italic_
                # Remove square brackets from links [text](url) -> text
                text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
                turn['text'] = text.strip()
        return dialogue_list

    def analyze_repo(self, blueprint):
        """
        Sends the blueprint to Gemini and returns the structured analysis.
        """
        if not self.model:
            return {
                "error": "API Key Missing",
                "roast_dialogue": [{"speaker": "System", "text": "Please configure GOOGLE_API_KEY."}],
                "mermaid_diagram": "graph TD; Error-->MissingKey",
                "developer_guide": "# Error\nAPI Key not configured."
            }

        prompt = generate_user_prompt(blueprint)
        
        try:
            # Configure safety settings to be permissible for "Roasting" (Satire)
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = self.model.generate_content(
                contents=[
                    {"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]} 
                ],
                generation_config={
                    "temperature": 0.8
                },
                safety_settings=safety_settings
            )
            
            # Check for safety blocks
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return {
                    "error": f"AI Blocked: {response.prompt_feedback.block_reason}",
                    "roast_dialogue": [{"speaker": "System", "text": "I am too polite to roast this code."}],
                    "mermaid_diagram": "graph TD; Blocked-->Safety",
                    "developer_guide": "# Safety Block\nThe AI refused to roast this repo."
                }

            try:
                raw_text = response.text
            except ValueError:
                # Often happens if response was blocked but prompt_feedback didn't catch it
                # or finish_reason is not STOP
                return {
                    "error": "AI Response Error (Likely Safety Block)",
                    "roast_dialogue": [{"speaker": "System", "text": "I can't say what I want to say."}],
                    "mermaid_diagram": "graph TD; Error-->Blocked",
                    "developer_guide": "# Error\nAI response was empty or blocked."
                }
            
            # Clean up potential markdown formatting
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            # Parse JSON
            result = json.loads(raw_text.strip())
            
            # Sanitize dialogue to remove markdown syntax
            if 'roast_dialogue' in result:
                result['roast_dialogue'] = self.sanitize_dialogue(result['roast_dialogue'])
            
            return result
            
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return {
                "error": str(e),
                "roast_dialogue": [{"speaker": "System", "text": "I choked on your spaghetti code."}],
                "mermaid_diagram": "graph TD; Error-->AI_Failed",
                "developer_guide": f"# Error\nAI processing failed: {e}"
            }

if __name__ == "__main__":
    # Test stub
    service = AIService()
    print("AI Service Initialized:", service.model is not None)
