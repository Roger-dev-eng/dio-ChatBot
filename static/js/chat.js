const API_BASE_URL = '/api';
let currentSessionId = null;
let isLoading = false;
let totalTokens = 0;

// Elementos DOM
let chatMessages, messageInput, sendButton, typingIndicator;
let useDocuments, temperatureSlider, maxTokensSlider;
let sessionInfo, tokenCounter, statusIndicator, modelInfo;
let settingsPanel, aboutModal;

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    initializeEventListeners();
    initializeSettings();
    checkAPIHealth();
    messageInput.focus();
    
    console.log('🚀 ChatBot Frontend inicializado!');
});

function initializeElements() {
    // Elementos principais
    chatMessages = document.getElementById('chatMessages');
    messageInput = document.getElementById('messageInput');
    sendButton = document.getElementById('sendButton');
    typingIndicator = document.getElementById('typingIndicator');
    
    // Configurações
    useDocuments = document.getElementById('useDocuments');
    temperatureSlider = document.getElementById('temperatureSlider');
    maxTokensSlider = document.getElementById('maxTokensSlider');
    
    // Informações
    sessionInfo = document.getElementById('sessionInfo');
    tokenCounter = document.getElementById('tokenCounter');
    statusIndicator = document.getElementById('statusIndicator');
    modelInfo = document.getElementById('modelInfo');
    
    // Modais e painéis
    settingsPanel = document.getElementById('settingsPanel');
    aboutModal = document.getElementById('aboutModal');
}

function initializeEventListeners() {
    // Input de mensagem
    messageInput.addEventListener('input', autoResize);
    messageInput.addEventListener('keydown', handleKeyPress);
    
    // Sliders
    temperatureSlider.addEventListener('input', updateTemperatureDisplay);
    maxTokensSlider.addEventListener('input', updateMaxTokensDisplay);
    
    // Clique fora do modal fecha ele
    aboutModal.addEventListener('click', function(e) {
        if (e.target === aboutModal) {
            hideAbout();
        }
    });
    
    // ESC fecha modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideAbout();
        }
    });
}

function initializeSettings() {
    updateTemperatureDisplay();
    updateMaxTokensDisplay();
}

// ============================================================================
// GERENCIAMENTO DE API
// ============================================================================

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            setAPIStatus(true);
            modelInfo.textContent = `Powered by ${data.model || 'GPT-4o-mini'}`;
            
            // Verificar se search está disponível
            if (!data.has_search) {
                useDocuments.disabled = true;
                useDocuments.parentElement.parentElement.title = 'Azure AI Search não configurado';
            }
        } else {
            throw new Error('API não saudável');
        }
    } catch (error) {
        setAPIStatus(false);
        modelInfo.textContent = 'Erro na conexão';
        console.error('Erro ao verificar API:', error);
    }
}

function setAPIStatus(online) {
    if (online) {
        statusIndicator.className = 'status-indicator';
        statusIndicator.title = 'API Online';
    } else {
        statusIndicator.className = 'status-indicator offline';
        statusIndicator.title = 'API Offline';
    }
}

// ============================================================================
// GERENCIAMENTO DE MENSAGENS
// ============================================================================

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isLoading) return;

    // Limpar input
    clearInput();

    // Adicionar mensagem do usuário
    addMessage(message, 'user');

    // Mostrar indicador de digitação
    showTyping();

    // Desabilitar envio
    setLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
                use_documents: useDocuments.checked,
                temperature: parseFloat(temperatureSlider.value),
                max_tokens: parseInt(maxTokensSlider.value)
            })
        });

        const data = await response.json();

        if (data.success) {
            // Atualizar sessão
            if (!currentSessionId) {
                currentSessionId = data.session_id;
                updateSessionInfo();
            }

            // Atualizar contador de tokens
            totalTokens += data.tokens_used || 0;
            updateTokenCounter();

            // Adicionar resposta do bot
            addMessage(data.response, 'bot', data.sources, {
                tokens: data.tokens_used,
                timestamp: data.timestamp
            });
        } else {
            addMessage(`❌ Erro: ${data.error}`, 'bot');
        }

    } catch (error) {
        addMessage('❌ Erro ao conectar com a API. Verifique se o servidor está rodando.', 'bot');
        console.error('Erro:', error);
        setAPIStatus(false);
    } finally {
        hideTyping();
        setLoading(false);
        messageInput.focus();
    }
}

function addMessage(content, role, sources = null, metadata = null) {
    // Remover mensagem de boas-vindas se existir
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = formatMessage(content);

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString('pt-BR');

    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageTime);

    // Adicionar fontes se disponíveis
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = `📖 <strong>Fontes:</strong> ${sources.join(', ')}`;
        messageDiv.appendChild(sourcesDiv);
    }

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function formatMessage(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace;">$1</code>')
        .replace(/```([\s\S]*?)```/g, '<pre style="background: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; margin: 8px 0;"><code>$1</code></pre>');
}

function showTyping() {
    typingIndicator.style.display = 'block';
    scrollToBottom();
}

function hideTyping() {
    typingIndicator.style.display = 'none';
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============================================================================
// CONTROLES DE INTERFACE
// ============================================================================

function setLoading(loading) {
    isLoading = loading;
    sendButton.disabled = loading;
    messageInput.disabled = loading;
    
    if (loading) {
        sendButton.innerHTML = '⏳';
    } else {
        sendButton.innerHTML = '➤';
    }
}

function autoResize() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function clearInput() {
    messageInput.value = '';
    messageInput.style.height = 'auto';
}

// ============================================================================
// GERENCIAMENTO DE SESSÃO
// ============================================================================

async function clearChat() {
    if (currentSessionId) {
        try {
            await fetch(`${API_BASE_URL}/session/${currentSessionId}/clear`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Erro ao limpar sessão:', error);
        }
    }
    
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>Chat Limpo! 🧹</h2>
            <p>Como posso ajudá-lo agora?</p>
        </div>
    `;
    
    totalTokens = 0;
    updateTokenCounter();
    updateSessionInfo();
}

async function newSession() {
    if (currentSessionId) {
        try {
            await fetch(`${API_BASE_URL}/session/${currentSessionId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Erro ao deletar sessão:', error);
        }
    }
    
    currentSessionId = null;
    totalTokens = 0;
    
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>Nova Sessão! 🆕</h2>
            <p>Vamos começar uma nova conversa!</p>
        </div>
    `;
    
    updateSessionInfo();
    updateTokenCounter();
    messageInput.focus();
}

function updateSessionInfo() {
    if (currentSessionId) {
        sessionInfo.textContent = `Sessão: ${currentSessionId.substring(0, 8)}...`;
    } else {
        sessionInfo.textContent = 'Sessão: Nova';
    }
}

function updateTokenCounter() {
    tokenCounter.textContent = `Tokens: ${totalTokens.toLocaleString('pt-BR')}`;
}

// ============================================================================
// CONFIGURAÇÕES
// ============================================================================

function toggleSettings() {
    if (settingsPanel.style.display === 'none' || !settingsPanel.style.display) {
        settingsPanel.style.display = 'block';
    } else {
        settingsPanel.style.display = 'none';
    }
}

function updateTemperatureDisplay() {
    const value = parseFloat(temperatureSlider.value);
    document.getElementById('temperatureValue').textContent = value.toFixed(1);
}

function updateMaxTokensDisplay() {
    const value = parseInt(maxTokensSlider.value);
    document.getElementById('maxTokensValue').textContent = value.toLocaleString('pt-BR');
}

// ============================================================================
// MODAL "SOBRE"
// ============================================================================

function showAbout() {
    aboutModal.style.display = 'flex';
}

function hideAbout() {
    aboutModal.style.display = 'none';
}

// ============================================================================
// MONITORAMENTO E MANUTENÇÃO
// ============================================================================

// Verificar API a cada 30 segundos
setInterval(checkAPIHealth, 30000);

// Salvar configurações no localStorage
function saveSettings() {
    const settings = {
        useDocuments: useDocuments.checked,
        temperature: temperatureSlider.value,
        maxTokens: maxTokensSlider.value
    };
    localStorage.setItem('chatbot-settings', JSON.stringify(settings));
}

function loadSettings() {
    try {
        const settings = JSON.parse(localStorage.getItem('chatbot-settings') || '{}');
        
        if (settings.useDocuments !== undefined) {
            useDocuments.checked = settings.useDocuments;
        }
        if (settings.temperature !== undefined) {
            temperatureSlider.value = settings.temperature;
            updateTemperatureDisplay();
        }
        if (settings.maxTokens !== undefined) {
            maxTokensSlider.value = settings.maxTokens;
            updateMaxTokensDisplay();
        }
    } catch (error) {
        console.warn('Erro ao carregar configurações:', error);
    }
}

// Salvar configurações quando mudarem
document.addEventListener('change', function(e) {
    if (e.target.matches('#useDocuments, #temperatureSlider, #maxTokensSlider')) {
        saveSettings();
    }
});

// Carregar configurações ao inicializar
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(loadSettings, 100);
});

// ============================================================================
// FUNCIONALIDADES EXTRAS
// ============================================================================

// Detectar se o usuário está offline
window.addEventListener('online', function() {
    checkAPIHealth();
    console.log('🌐 Conexão restaurada');
});

window.addEventListener('offline', function() {
    setAPIStatus(false);
    console.log('❌ Conexão perdida');
});

// Prevenir perda acidental de dados
window.addEventListener('beforeunload', function(e) {
    if (messageInput.value.trim() && messageInput.value.trim().length > 10) {
        e.preventDefault();
        e.returnValue = 'Você tem uma mensagem não enviada. Tem certeza que deseja sair?';
    }
});

// Atalhos de teclado
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter para enviar
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
    
    // Ctrl/Cmd + K para limpar chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        clearChat();
    }
    
    // Ctrl/Cmd + N para nova sessão
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        newSession();
    }
    
    // Ctrl/Cmd + , para abrir configurações
    if ((e.ctrlKey || e.metaKey) && e.key === ',') {
        e.preventDefault();
        toggleSettings();
    }
});

// Função para copiar mensagem
function copyMessage(element) {
    const messageContent = element.querySelector('.message-content');
    const text = messageContent.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        // Feedback visual
        const originalBg = messageContent.style.background;
        messageContent.style.background = 'rgba(34, 197, 94, 0.1)';
        
        setTimeout(() => {
            messageContent.style.background = originalBg;
        }, 500);
    }).catch(err => {
        console.error('Erro ao copiar:', err);
    });
}

// Adicionar botão de copiar nas mensagens
function addCopyButton(messageDiv) {
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-button';
    copyBtn.innerHTML = '📋';
    copyBtn.title = 'Copiar mensagem';
    copyBtn.onclick = () => copyMessage(messageDiv);
    
    messageDiv.addEventListener('mouseenter', () => {
        copyBtn.style.opacity = '1';
    });
    
    messageDiv.addEventListener('mouseleave', () => {
        copyBtn.style.opacity = '0';
    });
    
    messageDiv.appendChild(copyBtn);
}

// Modificar addMessage para incluir botão de copiar
const originalAddMessage = addMessage;
addMessage = function(content, role, sources = null, metadata = null) {
    originalAddMessage(content, role, sources, metadata);
    
    // Adicionar botão de copiar à última mensagem
    const messages = chatMessages.querySelectorAll('.message');
    const lastMessage = messages[messages.length - 1];
    if (lastMessage) {
        addCopyButton(lastMessage);
    }
};

// ============================================================================
// MELHORIAS DE EXPERIÊNCIA
// ============================================================================

// Animação suave para scroll
function smoothScrollToBottom() {
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

// Substituir scrollToBottom pela versão suave
scrollToBottom = smoothScrollToBottom;

// Contador de caracteres no input
messageInput.addEventListener('input', function() {
    const maxLength = 2000;
    const currentLength = messageInput.value.length;
    
    // Criar ou atualizar contador se não existir
    let counter = document.getElementById('charCounter');
    if (!counter) {
        counter = document.createElement('div');
        counter.id = 'charCounter';
        counter.style.cssText = `
            font-size: 0.75rem;
            color: #9ca3af;
            text-align: right;
            margin-top: 4px;
            padding-right: 4px;
        `;
        messageInput.parentElement.parentElement.appendChild(counter);
    }
    
    counter.textContent = `${currentLength}/${maxLength}`;
    
    // Mudar cor quando próximo do limite
    if (currentLength > maxLength * 0.9) {
        counter.style.color = '#ef4444';
    } else if (currentLength > maxLength * 0.7) {
        counter.style.color = '#f59e0b';
    } else {
        counter.style.color = '#9ca3af';
    }
});

// Placeholder dinâmico
const placeholders = [
    'Digite sua mensagem...',
    'Como posso ajudá-lo?',
    'Faça uma pergunta...',
    'Precisa de ajuda com algo?',
    'Conte-me o que você gostaria de saber...'
];

function rotatePlaceholder() {
    if (document.activeElement !== messageInput && !messageInput.value) {
        const randomPlaceholder = placeholders[Math.floor(Math.random() * placeholders.length)];
        messageInput.placeholder = randomPlaceholder;
    }
}

// Trocar placeholder a cada 10 segundos
setInterval(rotatePlaceholder, 10000);

// Resetar placeholder quando focar
messageInput.addEventListener('focus', function() {
    messageInput.placeholder = 'Digite sua mensagem...';
});

// ============================================================================
// EASTER EGGS E COMANDOS ESPECIAIS
// ============================================================================

function processSpecialCommands(message) {
    const lowerMessage = message.toLowerCase().trim();
    
    // Comandos especiais
    if (lowerMessage === '/help' || lowerMessage === '/ajuda') {
        addMessage(`
🆘 <strong>Comandos Disponíveis:</strong><br><br>
<strong>Interface:</strong><br>
• Ctrl/Cmd + Enter - Enviar mensagem<br>
• Ctrl/Cmd + K - Limpar chat<br>
• Ctrl/Cmd + N - Nova sessão<br>
• Ctrl/Cmd + , - Abrir configurações<br><br>
<strong>Especiais:</strong><br>
• /help ou /ajuda - Esta mensagem<br>
• /stats - Estatísticas da sessão<br>
• /clear - Limpar chat<br>
• /new - Nova sessão
        `, 'bot');
        return true;
    }
    
    if (lowerMessage === '/stats') {
        addMessage(`
📊 <strong>Estatísticas da Sessão:</strong><br><br>
• Tokens usados: ${totalTokens.toLocaleString('pt-BR')}<br>
• Sessão atual: ${currentSessionId ? currentSessionId.substring(0, 8) + '...' : 'Nova'}<br>
• Documentos: ${useDocuments.checked ? 'Ativados' : 'Desativados'}<br>
• Temperatura: ${temperatureSlider.value}<br>
• Max tokens: ${maxTokensSlider.value}
        `, 'bot');
        return true;
    }
    
    if (lowerMessage === '/clear') {
        clearChat();
        return true;
    }
    
    if (lowerMessage === '/new') {
        newSession();
        return true;
    }
    
    return false;
}

// Modificar sendMessage para processar comandos especiais
const originalSendMessage = sendMessage;
sendMessage = async function() {
    const message = messageInput.value.trim();
    
    // Verificar comandos especiais primeiro
    if (processSpecialCommands(message)) {
        clearInput();
        return;
    }
    
    // Processar mensagem normalmente
    await originalSendMessage();
};

// ============================================================================
// NOTIFICAÇÕES E FEEDBACK
// ============================================================================

function showNotification(message, type = 'info', duration = 3000) {
    // Remover notificação existente
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remover após duração especificada
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Adicionar CSS para animações de notificação
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .copy-button {
        position: absolute;
        top: -8px;
        right: -8px;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        border: none;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        font-size: 0.8rem;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 10;
    }
    
    .copy-button:hover {
        background: rgba(0, 0, 0, 0.9);
    }
    
    .message {
        position: relative;
    }
`;
document.head.appendChild(notificationStyles);

console.log('✅ ChatBot Frontend totalmente carregado com todas as funcionalidades!');