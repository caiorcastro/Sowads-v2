import google.generativeai as genai
import os

api_key = "AIzaSyBHMnc8R6tybytOO_cW6EDWqLfY4uLF6E0"
genai.configure(api_key=api_key)

print("Listing models...")
try:
    models = list(genai.list_models())
    if not models:
        print("No models found.")
    for m in models:
        print(f"Model: {m.name}")
except Exception as e:
    print(f"Error: {e}")
