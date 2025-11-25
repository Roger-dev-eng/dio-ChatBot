#  Chatbot IA com Flask

Este projeto é um chatbot inteligente construído utilizando **Flask**. O modelo de linguagem utilizado é o **LLaMA 3.1 8B Instant**, fornecido gratuitamente pela Groq.

## Objetivo do Projeto:
O objetivo deste chatbot é oferecer uma interface simples, rápida e intuitiva para interagir com um modelo de IA generativa.  
Ele permite que o usuário envie mensagens e receba respostas diretamente da API de inferência da Groq.

Inicialmente, o projeto foi desenvolvido utilizando **Azure Openai**, e posteriormentefoi migrado para a Groq.

##  Estrutura do Projeto

```
ChatBot/
│
├── app.py
├── .env
├── requirements.txt
│
├── chatbot_core/
│ ├── init.py
│ ├── chatbot.py
│ └── groq_client.py
│
└── frontend/
├── index.html
├── style.css
└── script.js
```
### 🔹 **app.py**
Servidor Flask que:
- expõe a rota `/api/chat` consumida pelo JavaScript
- conecta o backend ao modelo Groq

### 🔹 **chatbot_core/**
Contém toda a lógica do chatbot:
- integração com a API da Groq  
- formatação das mensagens  
- sistema de contexto básico  

### 🔹 **frontend/**
Interface visual do chat:
- página `index.html`
- estilos modernos em `style.css`
- envio de mensagens via JavaScript (`script.js`)

##  Como o rodar o sistema

1. Instale as dependências:
```bash
pip install -r requirements.txt
```
2. Configure sua chave da Groq:\
Crie o arquivo .env:
```bash
GROQ_API_KEY= SUA_CHAVE_AQUI
```
3. Rode o servidor:
```bash
python app.py
```
4. Abra no navegador:
```bash
http://127.0.0.1:5000
```
## Tecnologias Utilizadas
- Python 
- Flask  
- Flask-CORS  
- Groq API (LLaMA 3.1 8B Instant)  
- python-dotenv  
- HTML5  
- CSS3  
- JavaScript (fetch API)

#  Conclusão: 
Esta jornada demonstrou como transformar um código básico em uma aplicação completa e profissional. O processo ensinou muito além da programação, compreendemos inicialmente o ecossistema Azure AI Foundry, desde conceitos de tokens e custos até implementação de RAG com Azure AI Search. A partir disso, foi implementado diferentes outras tecnologias. Essa base sólida abre caminho para projetos mais ambiciosos com IA, sempre mantendo foco em qualidade.
