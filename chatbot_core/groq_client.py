import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def gerar_resposta(mensagens, temperature=0.7, max_tokens=300):
    resposta = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": "Você é um assistente útil."}] + mensagens,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resposta.choices[0].message.content
