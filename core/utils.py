import google.generativeai as genai
from django.conf import settings
from asgiref.sync import sync_to_async

# Configure Gemini with the API key from settings
if getattr(settings, 'GEMINI_API_KEY', None) and settings.GEMINI_API_KEY != 'your-api-key-here':
    genai.configure(api_key=settings.GEMINI_API_KEY)

def contains_profanity(text):
    """
    Checks if the provided text contains offensive, abusive, or inappropriate language
    in any language using Google Gemini.
    """
    if not text or not getattr(settings, 'GEMINI_API_KEY', None) or settings.GEMINI_API_KEY == 'your-api-key-here':
        return False
        
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = f"""
        You are a content moderation assistant.
        Does the following text contain offensive, abusive, or inappropriate language in ANY language?
        Reply with only: YES or NO

        Text: {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip().upper() == "YES"
    except Exception as e:
        # Fail open (allow post) if the API fails or is not configured properly
        print(f"Profanity filter error: {e}")
        return False


async def contains_profanity_async(text):
    """
    Async wrapper for contains_profanity, for use in WebSocket consumers.
    """
    return await sync_to_async(contains_profanity)(text)
