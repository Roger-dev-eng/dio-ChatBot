from .groq_client import gerar_resposta

class Chatbot:
    def chat(self, message):
        mensagens = [{"role": "user", "content": message}]
        return gerar_resposta(mensagens)
