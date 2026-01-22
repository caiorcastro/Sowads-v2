import google.generativeai as genai
import os

api_key = "AIzaSyBHMnc8R6tybytOO_cW6EDWqLfY4uLF6E0"
genai.configure(api_key=api_key)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(e)
