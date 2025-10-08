from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uvicorn
from src.agent import BankingAgent

app = FastAPI(title="Agente Bancario Virtual")

# Inicializar agente
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY no configurada")

agent = BankingAgent(api_key)

# Almacenar sesiones (en memoria simple)
sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal con chat interface"""
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏦 Agente Bancario Virtual</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                height: 600px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .header h1 { font-size: 24px; margin-bottom: 5px; }
            .header p { font-size: 14px; opacity: 0.9; }
            .chat-box {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .message {
                margin-bottom: 15px;
                display: flex;
                gap: 10px;
                animation: fadeIn 0.3s;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .message.user {
                justify-content: flex-end;
            }
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
            }
            .message.user .message-content {
                background: #667eea;
                color: white;
                border-bottom-right-radius: 4px;
            }
            .message.bot .message-content {
                background: white;
                color: #333;
                border-bottom-left-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .input-area {
                padding: 20px;
                background: white;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
            }
            #userInput {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            #userInput:focus {
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                cursor: pointer;
                font-weight: 600;
                transition: transform 0.2s;
            }
            button:hover {
                transform: scale(1.05);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 10px;
                color: #667eea;
            }
            .examples {
                padding: 10px 20px;
                background: #fff3cd;
                border-top: 1px solid #ffc107;
                font-size: 12px;
            }
            .examples strong { display: block; margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>�� Banco Nacional del Ecuador</h1>
                <p>Asistente Virtual Inteligente</p>
            </div>
            
            <div class="examples">
                <strong>💡 Prueba preguntar:</strong>
                "¿Horarios de atención?" • "¿Cómo abrir una cuenta?" • "Quiero ver mi saldo"
            </div>
            
            <div class="chat-box" id="chatBox">
                <div class="message bot">
                    <div class="message-content">
                        ¡Hola! 👋 Soy tu asistente virtual bancario. ¿En qué puedo ayudarte hoy?
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">Escribiendo...</div>
            
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Escribe tu mensaje aquí..." 
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()" id="sendBtn">Enviar</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('userInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Mostrar mensaje del usuario
                addMessage(message, 'user');
                input.value = '';
                
                // Deshabilitar input
                input.disabled = true;
                document.getElementById('sendBtn').disabled = true;
                document.getElementById('loading').style.display = 'block';
                
                try {
                    // Enviar al backend
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message })
                    });
                    
                    const data = await response.json();
                    
                    // Mostrar respuesta del bot
                    addMessage(data.response, 'bot');
                    
                } catch (error) {
                    addMessage('❌ Error al comunicarse con el servidor. Intenta de nuevo.', 'bot');
                }
                
                // Rehabilitar input
                input.disabled = false;
                document.getElementById('sendBtn').disabled = false;
                document.getElementById('loading').style.display = 'none';
                input.focus();
            }
            
            function addMessage(text, type) {
                const chatBox = document.getElementById('chatBox');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
                chatBox.appendChild(messageDiv);
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return html

@app.post("/chat")
async def chat(request: Request):
    """Endpoint para procesar mensajes"""
    try:
        data = await request.json()
        message = data.get('message', '')
        
        if not message:
            return JSONResponse({"error": "Mensaje vacío"}, status_code=400)
        
        # Procesar con el agente
        response = agent.process_message(message)
        
        return JSONResponse({
            "success": True,
            "response": response
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "response": f"Error: {str(e)}"
        }, status_code=500)

@app.get("/health")
async def health():
    """Health check para Render"""
    return {"status": "healthy", "service": "banking-ai-agent"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
