"""
Servidor Flask para interface web do chatbot
Gerencia rotas HTTP e integração com o módulo chatbot_core
"""
# Permite inicializar a API sem passar pelo terminal
import webbrowser
from threading import Timer

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

# Import do módulo do chatbot
from chatbot_core import get_chatbot, initialize_chatbot

# Inicializar Flask
app = Flask(__name__)

# Configurar CORS para permitir requisições do frontend
CORS(app, origins=["*"])  # Em produção, especificar domínios específicos

# Variável global para o chatbot
chatbot = None

# Função para abrir o navegador
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def init_app():
    """Inicializa o chatbot quando a aplicação inicia"""
    global chatbot
    try:
        chatbot = initialize_chatbot()
        print("✅ Flask + Chatbot inicializados com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar chatbot no Flask: {str(e)}")
        return False

# Inicializar na primeira requisição
@app.before_request
def before_first_request():
    global chatbot
    if chatbot is None:
        init_app()

# ============================================================================
# ROTAS WEB (Interface HTML)
# ============================================================================

@app.route('/')
def index():
    """Página principal - Interface do chat"""
    return render_template('chat.html')

# ============================================================================
# API ENDPOINTS (JSON)
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Endpoint principal para chat"""
    try:
        # Validar se chatbot está inicializado
        if not chatbot:
            return jsonify({
                "success": False,
                "error": "Chatbot não inicializado"
            }), 503
        
        # Obter dados da requisição
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Mensagem não fornecida"
            }), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({
                "success": False,
                "error": "Mensagem vazia"
            }), 400
        
        # Parâmetros opcionais
        session_id = data.get('session_id')
        use_documents = data.get('use_documents', False)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
        
        # Validar parâmetros
        if not (0.0 <= temperature <= 1.0):
            temperature = 0.7
        
        if not (100 <= max_tokens <= 4000):
            max_tokens = 2000
        
        # Processar chat
        result = chatbot.chat(
            message=message,
            session_id=session_id,
            use_documents=use_documents,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@app.route('/api/session/<session_id>', methods=['GET'])
def api_get_session(session_id):
    """Obtém informações de uma sessão específica"""
    try:
        if not chatbot:
            return jsonify({"error": "Chatbot não inicializado"}), 503
        
        session_info = chatbot.get_session_info(session_id)
        
        if not session_info:
            return jsonify({"error": "Sessão não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "session": session_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/<session_id>/clear', methods=['DELETE'])
def api_clear_session(session_id):
    """Limpa o histórico de uma sessão"""
    try:
        if not chatbot:
            return jsonify({"error": "Chatbot não inicializado"}), 503
        
        success = chatbot.clear_session(session_id)
        
        if not success:
            return jsonify({"error": "Sessão não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Sessão limpa com sucesso",
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/<session_id>', methods=['DELETE'])
def api_delete_session(session_id):
    """Remove uma sessão completamente"""
    try:
        if not chatbot:
            return jsonify({"error": "Chatbot não inicializado"}), 503
        
        success = chatbot.delete_session(session_id)
        
        if not success:
            return jsonify({"error": "Sessão não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Sessão removida com sucesso"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def api_list_sessions():
    """Lista todas as sessões ativas"""
    try:
        if not chatbot:
            return jsonify({"error": "Chatbot não inicializado"}), 503
        
        sessions = chatbot.list_sessions()
        
        return jsonify({
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """Endpoint de saúde da aplicação"""
    try:
        chatbot_status = chatbot is not None
        search_status = chatbot.has_search if chatbot else False
        
        return jsonify({
            "status": "healthy" if chatbot_status else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "chatbot_initialized": chatbot_status,
            "has_search": search_status,
            "model": chatbot.deployment if chatbot else None
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Retorna estatísticas da aplicação"""
    try:
        if not chatbot:
            return jsonify({"error": "Chatbot não inicializado"}), 503
        
        stats = chatbot.get_stats()
        
        return jsonify({
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Tratamento para páginas não encontradas"""
    if request.path.startswith('/api/'):
        return jsonify({
            "error": "Endpoint não encontrado",
            "status_code": 404
        }), 404
    return render_template('chat.html')

@app.errorhandler(405)
def method_not_allowed(error):
    """Tratamento para métodos HTTP não permitidos"""
    return jsonify({
        "error": "Método HTTP não permitido",
        "status_code": 405
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Tratamento para erros internos"""
    return jsonify({
        "error": "Erro interno do servidor",
        "status_code": 500
    }), 500

# ============================================================================
# CONFIGURAÇÕES E EXECUÇÃO
# ============================================================================

if __name__ == '__main__':
    # Configurações de desenvolvimento
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    print("=" * 60)
    print("🚀 Iniciando Azure OpenAI Chatbot...")
    print("=" * 60)
    
    # Inicializar chatbot antes de rodar servidor
    if init_app():
        print(f"🌐 URL: http://{host}:{port}")
        print(f"🔧 Debug: {debug_mode}")
        print(f"📱 Interface: http://{host}:{port}")
        print(f"🔌 API: http://{host}:{port}/api/")
        print("=" * 60)
        
        # Se o navegador ainda não estiver aberto, irá iniciar ele depois de 1 segundo
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            Timer(1, open_browser).start()
        
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True
        )
    else:
        print("❌ Falha ao inicializar. Verifique o arquivo .env")
        print("=" * 60)
