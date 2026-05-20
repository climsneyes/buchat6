import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:31b-cloud")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://pychat-25c45-default-rtdb.asia-southeast1.firebasedatabase.app/")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")

# Ollama cloud configuration
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma4:31b-cloud")
