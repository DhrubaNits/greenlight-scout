from google import genai
from google.genai.types import HttpOptions

client = genai.Client(
    http_options=HttpOptions(api_version="v1")
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Reply with exactly: Greenlight Scout Gemini connection works."
)

print(response.text)