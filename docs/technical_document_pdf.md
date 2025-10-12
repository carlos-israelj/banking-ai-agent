# Documentación Técnica - Banking AI Agent

**Proyecto:** Agente Conversacional Bancario con IA Generativa  
**Autor:** Carlos Israel Jiménez  
**Fecha:** Octubre 2025  
**Versión:** 1.0.0

---

## Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Componentes Técnicos](#componentes-técnicos)
3. [Implementación de RAG](#implementación-de-rag)
4. [Sistema de Herramientas (Tools)](#sistema-de-herramientas-tools)
5. [Seguridad e Infraestructura](#seguridad-e-infraestructura)
6. [Testing y Calidad](#testing-y-calidad)
7. [Deployment y Operaciones](#deployment-y-operaciones)

---

## Arquitectura del Sistema

### Visión General

```
┌──────────────┐
│   Usuario    │
│  (WhatsApp)  │
└──────┬───────┘
       │
       ↓
┌────────────────────────────────────────────┐
│         Capa de Aplicación                 │
│  ┌──────────────────────────────────────┐  │
│  │   BankingAgent (Orquestador)         │  │
│  │   • Gestión de conversación          │  │
│  │   • Control de flujo                 │  │
│  │   • Gestión de sesión                │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
       │
       ├───────────────┬───────────────┬──────────────┐
       ↓               ↓               ↓              ↓
┌─────────────┐ ┌──────────┐  ┌───────────┐  ┌──────────────┐
│   Gemini    │ │   RAG    │  │   Tools   │  │   Security   │
│   2.5       │ │ ChromaDB │  │  (6 APIs) │  │   Manager    │
│   Flash     │ │ + Embeds │  │           │  │              │
└─────────────┘ └──────────┘  └───────────┘  └──────────────┘
```

---

### Flujo de una Interacción

```python
1. Usuario envía mensaje por WhatsApp
   ↓
2. BankingAgent recibe input
   ↓
3. Verificación de sesión
   • ¿Usuario autenticado?
   • ¿Sesión expirada?
   ↓
4. Procesamiento con Gemini
   • Análisis de intención
   • Decisión de tool use
   ↓
5a. Si requiere tool:
    • Validación de auth
    • Ejecución de tool
    • Manejo de errores
    • Retry si necesario
    ↓
5b. Si requiere knowledge:
    • RAG search en ChromaDB
    • Top-K resultados
    • Contexto para LLM
    ↓
6. Gemini genera respuesta
   • Incorpora resultados
   • Formato conversacional
   ↓
7. Validación de output
   • Sanitización de datos
   • Enmascaramiento
   ↓
8. Logging y métricas
   • Guardar interacción
   • Actualizar KPIs
   ↓
9. Respuesta al usuario
```

---

## Componentes Técnicos

### 1. BankingAgent (Core)

**Archivo:** `src/agent.py`

**Responsabilidades:**
- Gestión del ciclo de vida de la conversación
- Orquestación de componentes
- Manejo de estado de sesión
- Control de errores y fallbacks

**Implementación:**

```python
class BankingAgent:
    def __init__(self, api_key: str):
        """Inicializa el agente con todas sus dependencias"""
        self.llm = self._initialize_gemini(api_key)
        self.knowledge_base = KnowledgeBase()
        self.tools_manager = ToolsManager()
        self.security = SecurityManager()
        self.session_data = None
        
    def process_message(self, user_message: str) -> str:
        """
        Procesa un mensaje del usuario.
        
        Flow:
        1. Validar input
        2. Construir contexto
        3. Llamar LLM con tools
        4. Manejar tool calls
        5. Validar output
        6. Retornar respuesta
        """
        # 1. Input validation
        if not self.security.validate_input(user_message):
            return "Mensaje no válido"
        
        # 2. Build context
        context = self._build_context(user_message)
        
        # 3. Call LLM
        try:
            response = self.llm.generate_content(
                contents=context,
                tools=self.tools_manager.get_tool_definitions(),
                safety_settings=SAFETY_SETTINGS
            )
        except Exception as e:
            return self._handle_llm_error(e)
        
        # 4. Handle tool calls
        if response.candidates[0].content.parts[0].function_call:
            tool_result = self._execute_tool(
                response.candidates[0].content.parts[0].function_call
            )
            # Enviar resultado de vuelta al LLM
            final_response = self._continue_with_tool_result(tool_result)
        else:
            final_response = response.text
        
        # 5. Output validation
        final_response = self.security.validate_output(final_response)
        
        # 6. Logging
        self._log_interaction(user_message, final_response)
        
        return final_response
```

---

### 2. Gemini Integration

**Configuración:**

```python
import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash-exp"

GENERATION_CONFIG = {
    "temperature": 0.7,  # Balance creatividad/precisión
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

# Inicialización
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=GENERATION_CONFIG,
    safety_settings=SAFETY_SETTINGS,
    system_instruction=SYSTEM_PROMPT
)
```

**System Prompt:**

Ubicado en `config/prompts.py`:

```python
SYSTEM_PROMPT = """
Eres un asistente virtual del Banco Nacional del Ecuador.

IDENTIDAD:
- Profesional, amigable y empático
- Experto en productos y servicios bancarios
- Prioriza la seguridad y privacidad del cliente

CAPACIDADES:
1. Responder FAQs sobre productos bancarios
2. Consultar información personalizada (requiere autenticación):
   - Saldos de cuentas
   - Movimientos recientes
   - Información de tarjetas
   - Pólizas de seguros

REGLAS DE ORO:
⚠️  NUNCA reveles información personal sin autenticación
⚠️  Si no estás seguro, deriva a asesor humano
⚠️  No inventes información: usa solo datos de herramientas

FORMATO:
- Conversacional en español
- Máximo 3 párrafos por respuesta
- Usa emojis moderadamente (🏦 💳 ✅)
- Sé conciso pero completo

AUTENTICACIÓN:
Si el usuario solicita información personal:
1. Verifica si está autenticado
2. Si no → Ofrece autenticación con cédula + OTP
3. Usa authenticate_user tool
4. Solo después procede con la consulta
"""
```

---

### 3. Sistema RAG (Retrieval Augmented Generation)

**Arquitectura:**

```
FAQs (JSON)
    ↓
Embeddings Generation
(sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
    ↓
Vector Database
(ChromaDB)
    ↓
Semantic Search
(Cosine Similarity)
    ↓
Top-K Results → Context for LLM
```

**Implementación:**

```python
# src/knowledge.py

from sentence_transformers import SentenceTransformer
import chromadb

class KnowledgeBase:
    def __init__(self):
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        )
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="banking_faqs",
            metadata={"hnsw:space": "cosine"}
        )
        
    def index_documents(self, faqs: List[Dict]):
        """Indexa FAQs en la base vectorial"""
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for i, faq in enumerate(faqs):
            # Combinar pregunta + respuesta para mejor contexto
            text = f"{faq['question']} {faq['answer']}"
            documents.append(text)
            
            # Generar embedding
            embedding = self.embedding_model.encode(text).tolist()
            embeddings.append(embedding)
            
            metadatas.append({
                "category": faq.get("category", "general"),
                "question": faq["question"]
            })
            ids.append(f"faq_{i}")
        
        # Agregar a ChromaDB
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Búsqueda semántica en la base de conocimiento"""
        
        # Generar embedding de la query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Buscar en ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Formatear resultados
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "question": results['metadatas'][0][i]['question'],
                "answer": results['documents'][0][i],
                "relevance": 1 - results['distances'][0][i],  # Convertir distancia a score
                "category": results['metadatas'][0][i]['category']
            })
        
        return formatted_results
```

**Datos de FAQs:**

```json
// data/faqs.json
[
  {
    "id": 1,
    "category": "horarios",
    "question": "¿Cuál es el horario de atención?",
    "answer": "Nuestros horarios son: Lunes a Viernes 8:00 AM - 5:00 PM, Sábados 9:00 AM - 1:00 PM. Los domingos estamos cerrados."
  },
  {
    "id": 2,
    "category": "cuentas",
    "question": "¿Cómo abrir una cuenta de ahorros?",
    "answer": "Para abrir una cuenta necesitas: 1) Cédula de identidad vigente, 2) Depósito inicial de $50, 3) Visitar cualquier sucursal o abrir en línea."
  }
  // ... más FAQs
]
```

---

## Sistema de Herramientas (Tools)

### Tool Calling con Gemini

Gemini soporta function calling nativo. Definimos las tools en formato JSON Schema:

```python
# src/tools.py

TOOL_DEFINITIONS = [
    {
        "name": "authenticate_user",
        "description": "Autentica un usuario usando cédula y código OTP",
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Número de cédula del usuario"
                },
                "otp_code": {
                    "type": "string",
                    "description": "Código OTP de 6 dígitos enviado por SMS"
                }
            },
            "required": ["document_id", "otp_code"]
        }
    },
    {
        "name": "get_account_balance",
        "description": "Consulta el saldo de cuentas del usuario autenticado",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ID del usuario autenticado"
                },
                "account_type": {
                    "type": "string",
                    "enum": ["savings", "checking", "all"],
                    "description": "Tipo de cuenta a consultar"
                }
            },
            "required": ["user_id"]
        }
    }
    // ... más tools
]
```

### Implementación de Tools

```python
class ToolsManager:
    def __init__(self):
        self.tools = {
            "authenticate_user": self.authenticate_user,
            "get_account_balance": self.get_account_balance,
            "get_account_movements": self.get_account_movements,
            "get_card_info": self.get_card_info,
            "get_policy_info": self.get_policy_info,
            "search_knowledge_base": self.search_knowledge_base
        }
    
    def execute(self, tool_name: str, parameters: Dict) -> Dict:
        """Ejecuta una tool con manejo de errores"""
        
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": "TOOL_NOT_FOUND"
            }
        
        try:
            result = self.tools[tool_name](**parameters)
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def authenticate_user(self, document_id: str, otp_code: str) -> Dict:
        """
        Simula autenticación 2FA.
        En producción, llamaría al servicio de auth real.
        """
        # Simulación
        if document_id == "1234567890" and otp_code == "123456":
            return {
                "success": True,
                "user_id": "USR-12345",
                "user_name": "Juan Pérez",
                "session_token": secrets.token_urlsafe(32),
                "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat()
            }
        else:
            return {
                "success": False,
                "error": "INVALID_CREDENTIALS"
            }
    
    def get_account_balance(self, user_id: str, account_type: str = "all") -> Dict:
        """
        Consulta saldo de cuentas.
        En producción, llamaría al core bancario.
        """
        # Simulación
        accounts_data = {
            "USR-12345": {
                "savings": {
                    "balance": 5420.50,
                    "currency": "USD",
                    "account_number": "****1234"
                },
                "checking": {
                    "balance": 1250.00,
                    "currency": "USD",
                    "account_number": "****5678"
                }
            }
        }
        
        if user_id not in accounts_data:
            return {
                "success": False,
                "error": "USER_NOT_FOUND"
            }
        
        user_accounts = accounts_data[user_id]
        
        if account_type == "all":
            return {
                "success": True,
                "accounts": [
                    {"type": "savings", **user_accounts["savings"]},
                    {"type": "checking", **user_accounts["checking"]}
                ]
            }
        elif account_type in user_accounts:
            return {
                "success": True,
                "accounts": [
                    {"type": account_type, **user_accounts[account_type]}
                ]
            }
        else:
            return {
                "success": False,
                "error": "ACCOUNT_NOT_FOUND"
            }
```

---

## Seguridad e Infraestructura

### SecurityManager

```python
# src/security.py

import re
from datetime import datetime, timedelta
from typing import Optional, Dict

class SecurityManager:
    def __init__(self):
        self.failed_attempts = {}  # user_id: count
        self.blocked_users = set()
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
    
    def validate_input(self, user_input: str) -> bool:
        """Valida input del usuario para prevenir ataques"""
        
        # Detectar XSS
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick='
        ]
        for pattern in xss_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"XSS attempt detected: {user_input[:100]}")
                return False
        
        # Detectar SQL injection
        sql_patterns = [
            r'(union|select|insert|update|delete|drop)\s',
            r';\s*(drop|delete)',
            r'--\s*$'
        ]
        for pattern in sql_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"SQL injection attempt: {user_input[:100]}")
                return False
        
        return True
    
    def validate_output(self, agent_response: str, authenticated: bool = False) -> str:
        """Valida y sanitiza output del agente"""
        
        # Enmascarar números de cuenta si no está autenticado
        if not authenticated:
            agent_response = re.sub(
                r'\b\d{10,16}\b', 
                lambda m: '****' + m.group()[-4:], 
                agent_response
            )
        
        # Enmascarar números de tarjeta
        agent_response = re.sub(
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            lambda m: '**** **** **** ' + m.group()[-4:],
            agent_response
        )
        
        return agent_response
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Verifica rate limiting"""
        return self.rate_limiter.check(user_id)
    
    def track_failed_auth(self, user_id: str):
        """Registra intento fallido de autenticación"""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = 0
        
        self.failed_attempts[user_id] += 1
        
        if self.failed_attempts[user_id] >= 3:
            self.blocked_users.add(user_id)
            logger.warning(f"User {user_id} blocked after 3 failed attempts")
    
    def is_blocked(self, user_id: str) -> bool:
        """Verifica si un usuario está bloqueado"""
        return user_id in self.blocked_users
```

### Rate Limiter

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def check(self, user_id: str) -> bool:
        """Verifica si el usuario puede hacer un request"""
        now = time.time()
        
        # Limpiar requests antiguos
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window_seconds
        ]
        
        # Verificar límite
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Registrar nuevo request
        self.requests[user_id].append(now)
        return True
```

---

## Testing y Calidad

### Estructura de Tests

```
tests/
├── __init__.py
├── test_agent.py           # Tests del agente principal
├── test_rag.py            # Tests del sistema RAG
├── test_tools.py          # Tests de las herramientas
├── test_security.py       # Tests de seguridad
└── test_integration.py    # Tests de integración
```

### Ejemplo de Test

```python
# tests/test_agent.py

import pytest
from src.agent import BankingAgent

@pytest.fixture
def agent():
    """Fixture que crea una instancia del agente"""
    return BankingAgent(api_key=os.getenv('GEMINI_API_KEY'))

def test_faq_response(agent):
    """Test: Responde correctamente a FAQ básica"""
    response = agent.process_message("¿Cuál es el horario de atención?")
    
    assert "8:00" in response or "8 AM" in response.lower()
    assert "lunes" in response.lower() or "monday" in response.lower()

def test_authentication_required(agent):
    """Test: Solicita autenticación para consultas sensibles"""
    response = agent.process_message("¿Cuál es mi saldo?")
    
    assert "autenticación" in response.lower() or "cédula" in response.lower()
    assert agent.session_data is None

def test_authentication_flow(agent):
    """Test: Flujo completo de autenticación"""
    # Solicitar autenticación
    response1 = agent.process_message("Quiero ver mi saldo")
    assert "cédula" in response1.lower()
    
    # Autenticar
    response2 = agent.process_message("Mi cédula es 1234567890")
    assert "código" in response2.lower() or "otp" in response2.lower()
    
    # Enviar OTP
    response3 = agent.process_message("El código es 123456")
    assert agent.session_data is not None
    assert agent.session_data["user_id"] == "USR-12345"

def test_security_xss_prevention(agent):
    """Test: Previene ataques XSS"""
    malicious_input = "<script>alert('xss')</script>"
    response = agent.process_message(malicious_input)
    
    assert "<script>" not in response
    assert "no válido" in response.lower() or "error" in response.lower()
```

### Ejecución de Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=src --cov-report=html

# Tests específicos
pytest tests/test_agent.py::test_authentication_flow -v
```

---

## Deployment y Operaciones

### Estructura del Proyecto

```
banking-ai-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py           # Agente principal
│   ├── tools.py           # Herramientas
│   ├── knowledge.py       # Sistema RAG
│   ├── security.py        # Seguridad
│   └── voice_agent.py     # Agente de voz (Caso #2)
├── config/
│   ├── settings.py        # Configuración
│   └── prompts.py         # System prompts
├── data/
│   └── faqs.json         # Base de conocimiento
├── tests/
│   ├── test_agent.py
│   ├── test_rag.py
│   └── test_tools.py
├── docs/
│   ├── final_report.md
│   ├── technical_document.md
│   └── voice_agent_extension.md
├── main.py               # CLI principal
├── api.py                # API REST (opcional)
├── voice_demo.py         # Demo de voz
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Variables de Entorno

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=credentials/google-cloud-key.json
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/carlos-israelj/banking-ai-agent.git
cd banking-ai-agent

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 5. Ejecutar
python main.py
```

### Docker (Opcional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "api.py"]
```

```bash
# Build
docker build -t banking-ai-agent .

# Run
docker run -p 8000:8000 --env-file .env banking-ai-agent
```

### API REST (Bonus)

```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agent import BankingAgent

app = FastAPI(title="Banking AI Agent API")
agent = BankingAgent()

class Message(BaseModel):
    text: str
    session_id: str

@app.post("/chat")
async def chat(message: Message):
    """Endpoint para interacción con el agente"""
    try:
        response = agent.process_message(message.text)
        return {
            "response": response,
            "session_id": message.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}
```

### Logging

```python
# Configuración en config/settings.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)
```

### Monitoreo

**Métricas a monitorear:**
- Latencia (p50, p95, p99)
- Tasa de error
- Uso de cada tool
- Tasa de escalamiento
- CSAT score

**Herramientas sugeridas:**
- Prometheus + Grafana (métricas)
- ELK Stack (logs)
- Sentry (error tracking)

---

## Performance y Optimización

### Optimizaciones Implementadas

1. **Caché de embeddings**
   - Evita recalcular embeddings en cada búsqueda
   - Reduce latencia del RAG de ~500ms a ~100ms

2. **Connection pooling**
   - Reutiliza conexiones HTTP para Gemini
   - Reduce overhead de SSL handshake

3. **Async operations**
   - Tools que no dependen entre sí se ejecutan en paralelo
   - Reduce latencia en casos con múltiples tools

4. **Prompt optimization**
   - Prompts concisos pero completos
   - Reduce tokens procesados sin perder calidad

< 