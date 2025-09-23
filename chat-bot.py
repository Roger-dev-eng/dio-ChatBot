import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Carregar variáveis do arquivo .env
load_dotenv()

class AzureChatBot:
    def __init__(self):
        """Inicializa o chatbot com configurações do Azure OpenAI"""
        self.endpoint = os.getenv("ENDPOINT_URL", "https://r0663-mfwsitny-swedencentral.cognitiveservices.azure.com/")
        self.deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")
        self.api_key = os.getenv("AZURE_OPENAI_KEY")
        
        # Verificar se temos chave de API ou usar autenticação AD
        if self.api_key:
            # Usar autenticação por chave
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version="2025-01-01-preview",
            )
            print("🔑 Usando autenticação por chave de API")
        else:
            # Usar autenticação Azure AD (requer az login)
            try:
                self.token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(), 
                    "https://cognitiveservices.azure.com/.default"
                )
                
                self.client = AzureOpenAI(
                    azure_endpoint=self.endpoint,
                    azure_ad_token_provider=self.token_provider,
                    api_version="2025-01-01-preview",
                )
                print("🔐 Usando autenticação Azure AD")
            except Exception as e:
                raise Exception(f"Erro na autenticação. Instale Azure CLI (az login) ou configure AZURE_OPENAI_KEY. Erro: {str(e)}")
        
        # Histórico da conversa
        self.conversation_history = [
            {
                "role": "system",
                "content": "Você é um assistente de IA útil e amigável. Responda de forma clara e objetiva, mantendo um tom conversacional e profissional. Se não souber algo, seja honesto sobre isso."
            }
        ]
        
        print("🤖 Chatbot Azure OpenAI inicializado!")
        print("💡 Digite 'sair' para encerrar, 'limpar' para limpar histórico, 'historico' para ver conversas")
        print("-" * 60)

    def get_response(self, user_message):
        """Obtém resposta do modelo Azure OpenAI"""
        try:
            # Adicionar mensagem do usuário ao histórico
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Fazer chamada para Azure OpenAI
            completion = self.client.chat.completions.create(
                model=self.deployment,
                messages=self.conversation_history,
                max_tokens=2000,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )
            
            # Extrair resposta
            response = completion.choices[0].message.content
            
            # Adicionar resposta ao histórico
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
            
        except Exception as e:
            return f"❌ Erro ao obter resposta: {str(e)}"

    def clear_history(self):
        """Limpa o histórico da conversa mantendo apenas o prompt do sistema"""
        self.conversation_history = self.conversation_history[:1]  # Manter apenas system message
        print("🧹 Histórico limpo!")

    def show_history(self):
        """Mostra o histórico da conversa"""
        print("\n📚 Histórico da Conversa:")
        print("-" * 40)
        
        for i, message in enumerate(self.conversation_history[1:], 1):  # Skip system message
            role = "👤 Você" if message["role"] == "user" else "🤖 Bot"
            content = message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"]
            print(f"{i}. {role}: {content}")
        
        print("-" * 40)

    def save_conversation(self, filename=None):
        """Salva a conversa em um arquivo JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversa_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            print(f"💾 Conversa salva em: {filename}")
        except Exception as e:
            print(f"❌ Erro ao salvar conversa: {str(e)}")

    def run(self):
        """Executa o loop principal do chatbot"""
        print("💬 Comece a conversar!")
        
        while True:
            try:
                # Obter entrada do usuário
                user_input = input("\n👤 Você: ").strip()
                
                # Verificar comandos especiais
                if user_input.lower() in ['sair', 'quit', 'exit']:
                    print("👋 Obrigado por usar o chatbot! Até logo!")
                    break
                
                elif user_input.lower() in ['limpar', 'clear']:
                    self.clear_history()
                    continue
                
                elif user_input.lower() in ['historico', 'history']:
                    self.show_history()
                    continue
                
                elif user_input.lower() in ['salvar', 'save']:
                    self.save_conversation()
                    continue
                
                elif user_input.lower() in ['ajuda', 'help']:
                    print("\n🆘 Comandos disponíveis:")
                    print("- 'sair': Encerra o chatbot")
                    print("- 'limpar': Limpa o histórico da conversa")
                    print("- 'historico': Mostra o histórico da conversa")
                    print("- 'salvar': Salva a conversa em arquivo JSON")
                    print("- 'ajuda': Mostra esta mensagem")
                    continue
                
                elif not user_input:
                    print("⚠️  Digite uma mensagem!")
                    continue
                
                # Obter e exibir resposta
                print("🤖 Bot: ", end="", flush=True)
                response = self.get_response(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chatbot encerrado pelo usuário!")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {str(e)}")

def main():
    """Função principal"""
    try:
        chatbot = AzureChatBot()
        chatbot.run()
    except Exception as e:
        print(f"❌ Erro ao inicializar chatbot: {str(e)}")
        print("💡 Verifique se as variáveis de ambiente ENDPOINT_URL e DEPLOYMENT_NAME estão configuradas")
        print("💡 Verifique se você está autenticado no Azure (az login)")

if __name__ == "__main__":
    main()