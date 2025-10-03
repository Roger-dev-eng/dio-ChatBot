"""
Módulo principal do chatbot Azure OpenAI
Contém toda a lógica de integração com Azure OpenAI e Azure AI Search
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Carregar variáveis do arquivo .env
load_dotenv()

class ChatMessage:
    """Representa uma mensagem no chat"""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }

class ChatSession:
    """Gerencia uma sessão de chat individual"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()
        self.message_count = 0
        
        # Adicionar mensagem do sistema
        self.messages.append(
            ChatMessage(
                role="system",
                content="Você é um assistente de IA útil e amigável. Responda de forma clara e objetiva."
            )
        )
    
    def add_message(self, role: str, content: str):
        """Adiciona uma mensagem à sessão"""
        message = ChatMessage(role, content)
        self.messages.append(message)
        self.last_activity = datetime.now().isoformat()
        
        if role == "user":
            self.message_count += 1
    
    def get_messages_for_api(self):
        """Retorna mensagens no formato da API OpenAI"""
        return [msg.to_dict() for msg in self.messages]
    
    def clear_history(self):
        """Limpa o histórico mantendo apenas a mensagem do sistema"""
        system_message = self.messages[0]
        self.messages = [system_message]
        self.message_count = 0
        self.last_activity = datetime.now().isoformat()
    
    def get_info(self):
        """Retorna informações da sessão"""
        return {
            "session_id": self.session_id,
            "message_count": self.message_count,
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }

class AzureChatBot:
    """Classe principal do chatbot Azure OpenAI"""
    
    def __init__(self):
        """Inicializa o chatbot com configurações do Azure"""
        self._load_config()
        self._initialize_client()
        self._initialize_sessions()
        
        print(f"🤖 Azure OpenAI Chatbot inicializado!")
        print(f"📊 Modelo: {self.deployment}")
        print(f"📚 Azure AI Search: {'Ativo' if self.has_search else 'Inativo'}")
    
    def _load_config(self):
        """Carrega configurações das variáveis de ambiente"""
        # Configurações obrigatórias
        self.endpoint = os.getenv("ENDPOINT_URL")
        self.deployment = os.getenv("DEPLOYMENT_NAME")
        self.api_key = os.getenv("AZURE_OPENAI_KEY")
        
        # Validar configurações obrigatórias
        if not all([self.endpoint, self.deployment, self.api_key]):
            missing = []
            if not self.endpoint: missing.append("ENDPOINT_URL")
            if not self.deployment: missing.append("DEPLOYMENT_NAME") 
            if not self.api_key: missing.append("AZURE_OPENAI_KEY")
            
            raise ValueError(f"Configurações obrigatórias não encontradas: {', '.join(missing)}")
        
        # Configurações opcionais do Azure AI Search
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX")
        
        # Verificar se Azure AI Search está disponível
        self.has_search = all([
            self.search_endpoint, 
            self.search_key, 
            self.search_index
        ])
    
    def _initialize_client(self):
        """Inicializa o cliente Azure OpenAI"""
        try:
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version="2025-01-01-preview",
            )
        except Exception as e:
            raise Exception(f"Erro ao inicializar cliente Azure OpenAI: {str(e)}")
    
    def _initialize_sessions(self):
        """Inicializa o gerenciamento de sessões"""
        # Em produção, usar Redis ou banco de dados
        self.sessions: Dict[str, ChatSession] = {}
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        """Obtém sessão existente ou cria uma nova"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        # Criar nova sessão
        new_session_id = session_id or str(uuid.uuid4())
        session = ChatSession(new_session_id)
        self.sessions[new_session_id] = session
        
        return session
    
    def chat(self, message: str, session_id: Optional[str] = None, 
             use_documents: bool = False, temperature: float = 0.7, 
             max_tokens: int = 2000) -> dict:
        """
        Processa uma mensagem de chat
        
        Args:
            message: Mensagem do usuário
            session_id: ID da sessão (opcional)
            use_documents: Se deve usar documentos via Azure AI Search
            temperature: Criatividade da resposta (0.0 a 1.0)
            max_tokens: Máximo de tokens na resposta
            
        Returns:
            dict: Resposta com informações da conversa
        """
        try:
            # Obter ou criar sessão
            session = self.get_or_create_session(session_id)
            
            # Adicionar mensagem do usuário
            session.add_message("user", message)
            
            # Preparar parâmetros da chamada
            completion_params = {
                "model": self.deployment,
                "messages": session.get_messages_for_api(),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            # Configurar Azure AI Search se solicitado
            sources = []
            if use_documents and self.has_search:
                completion_params["extra_body"] = self._get_search_config()
            
            # Fazer chamada para Azure OpenAI
            completion = self.client.chat.completions.create(**completion_params)
            
            # Processar resposta
            response_content = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else 0
            
            # Processar citações se disponíveis
            if (hasattr(completion.choices[0].message, 'context') and 
                completion.choices[0].message.context):
                citations = completion.choices[0].message.context.get('citations', [])
                sources = [citation.get('title', 'Documento') for citation in citations[:3]]
            
            # Adicionar resposta à sessão
            session.add_message("assistant", response_content)
            
            return {
                "success": True,
                "response": response_content,
                "session_id": session.session_id,
                "tokens_used": tokens_used,
                "sources": sources if sources else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_search_config(self) -> dict:
        """Retorna configuração do Azure AI Search"""
        return {
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": self.search_endpoint,
                        "index_name": self.search_index,
                        "authentication": {
                            "type": "api_key",
                            "key": self.search_key
                        },
                        "top_n_documents": 5,
                        "in_scope": True,
                        "strictness": 3,
                        "role_information": "Responda baseado nos documentos fornecidos."
                    }
                }
            ]
        }
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Obtém informações de uma sessão"""
        if session_id not in self.sessions:
            return None
        
        return self.sessions[session_id].get_info()
    
    def clear_session(self, session_id: str) -> bool:
        """Limpa o histórico de uma sessão"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].clear_history()
        return True
    
    def list_sessions(self) -> List[dict]:
        """Lista todas as sessões ativas"""
        return [session.get_info() for session in self.sessions.values()]
    
    def delete_session(self, session_id: str) -> bool:
        """Remove uma sessão completamente"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_stats(self) -> dict:
        """Retorna estatísticas gerais"""
        total_sessions = len(self.sessions)
        total_messages = sum(session.message_count for session in self.sessions.values())
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "has_search": self.has_search,
            "model": self.deployment
        }

# Instância global do chatbot (singleton)
_chatbot_instance = None

def get_chatbot() -> AzureChatBot:
    """Retorna instância do chatbot (singleton)"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = AzureChatBot()
    return _chatbot_instance

def initialize_chatbot() -> AzureChatBot:
    """Inicializa o chatbot (usado pelo Flask)"""
    try:
        return get_chatbot()
    except Exception as e:
        print(f"❌ Erro ao inicializar chatbot: {str(e)}")
        raise