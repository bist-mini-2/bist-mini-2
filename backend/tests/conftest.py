import os

# Set mock API key to prevent LangChain from raising environment validation errors during test collection
os.environ.setdefault("OPENAI_API_KEY", "mock-key-for-test-collection")
