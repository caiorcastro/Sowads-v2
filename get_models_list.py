import google.generativeai as genai
import os

api_key = "AIzaSyBHMnc8R6tybytOO_cW6EDWqLfY4uLF6E0"
genai.configure(api_key=api_key)

try:
    with open('modelos/modelos_disponiveis.txt', 'w') as f:
        f.write("Modelos Disponíveis para sua Chave:\n")
        f.write("===================================\n")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"- {m.name}\n")
    print("Models listed in models/modelos_disponiveis.txt")
except Exception as e:
    print(f"Error: {e}")
