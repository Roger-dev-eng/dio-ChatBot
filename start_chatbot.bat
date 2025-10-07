@echo off
echo 🚀 Iniciando Azure OpenAI Chatbot...
cd /d %~dp0

REM Executa o Flask em background e fecha o CMD
start /min pythonw app.py
exit
