# 🏦 Banking AI Agent

Agente conversacional inteligente para atención bancaria usando IA Generativa (Gemini 2.5 Flash) con capacidades de voz.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Demo Rápido](#-demo-rápido)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Arquitectura](#-arquitectura)
- [Documentación](#-documentación)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ Características

### Caso #1: Agente Bancario Conversacional

- 🤖 **IA Generativa:** Powered by Gemini 2.5 Flash
- 🔧 **6 Tools Funcionales:** Autenticación, consultas de saldo, movimientos, tarjetas, pólizas
- 📚 **RAG (Retrieval Augmented Generation):** Base de conocimiento con FAQs usando ChromaDB
- 🔒 **Seguridad Multinivel:** 2FA, rate limiting, input/output validation
- 💬 **Conversación Natural:** Comprende lenguaje coloquial en español
- 📊 **Métricas y Logging:** Tracking completo de interacciones

### Caso #2: Agente de Voz (Opcional)

- 🎙️ **Text-to-Speech:** Google Cloud TTS con voces naturales en español
- 🔊 **Audio Real:** Genera archivos MP3 funcionales
- 🔄 **Integración Completa:** Reutiliza el agente bancario base
- 📞 **Arquitectura para Telefonía:** Diseñado para Twilio/Vonage
- ⚡ **Baja Latencia:** <3 segundos end-to-end

### Extras

- 🚀 **API REST:** Endpoint HTTP con FastAPI (bonus)
- 🧪 **Tests Automatizados:** Cobertura con pytest
- 🐳 **Docker Ready:** Dockerfile incluido
- 📖 **Documentación Completa:** 3 documentos técnicos detallados

---

## 🎬 Demo Rápido

```bash
# Clonar repositorio
git clone https://github.com/carlos-israelj/banking-ai-agent.git
cd banking-ai-agent

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key (ver sección Configuración)
cp .env.example .env
# Editar .env con tu GEMINI_API_KEY

# Ejecutar agente conversacional
python main.py

# O ejecutar demo de voz
python voice_demo.py
```

**Ejemplo de conversación:**

```
Usuario: Hola
Agente: ¡Hola! 👋 Soy tu asistente virtual del Banco Nacional. 
        ¿En qué puedo ayudarte?

Usuario: ¿Cuál es el horario de atención?
Agente: Nuestros horarios son:
        • Lunes a Viernes: 8:00 AM - 5:00 PM
        • Sábados: 9:00 AM - 1:00 PM
        • Domingos: Cerrado

Usuario: Quiero ver mi saldo
Agente: Para consultarlo, necesito verificar tu identidad.
        ¿Puedes proporcionarme tu número de cédula? 🔐
```

---

## 📦 Instalación

### Requisitos del Sistema

- **Python:** 3.11 o superior
- **Sistema Operativo:** Linux, macOS, Windows (con WSL recomendado)
- **RAM:** Mínimo 4GB
- **Espacio en disco:** ~500MB (con dependencias)

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/carlos-israelj/banking-ai-agent.git
cd banking-ai-agent
```

### Paso 2: Crear Entorno Virtual

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Windows (CMD)
python -m venv venv
venv\Scripts\activate.bat
```

### Paso 3: Instalar Dependencias

```bash
# Instalación completa (incluye voz)
pip install -r requirements.txt

# Solo agente conversacional (sin voz)
pip install google-generativeai python-dotenv
```

### Verificar Instalación

```bash
python -c "import google.generativeai as genai; print('✅ Instalación exitosa')"
```

---

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```bash
# ============================================
# CASO #1: AGENTE BANCARIO
# ============================================

# API Key de Google AI (Gemini)
# Obtener en: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=tu_api_key_aqui

# Configuración opcional
LOG_LEVEL=INFO
ENVIRONMENT=development

# ============================================
# CASO #2: AGENTE DE VOZ (OPCIONAL)
# ============================================

# Credenciales de Google Cloud (archivo JSON)
# Solo necesario si vas a usar el agente de voz
GOOGLE_APPLICATION_CREDENTIALS=credentials/google-cloud-key.json
```

### 2. Obtener API Key de Gemini

1. Ve a https://aistudio.google.com/app/apikey
2. Click en **"Create API Key"**
3. Selecciona proyecto o crea uno nuevo
4. Copia la key y pégala en tu `.env`

**⚠️ IMPORTANTE:** Nunca compartas tu API key públicamente.

### 3. (Opcional) Configurar Google Cloud para Voz

Si quieres probar el agente de voz con TTS/STT real:

#### Opción A: Con Service Account (Recomendado)

1. Ve a https://console.cloud.google.com/
2. Crea un proyecto o selecciona uno existente
3. Habilita las APIs:
   - Text-to-Speech API
   - Speech-to-Text API
4. Crea Service Account:
   - **IAM & Admin** → **Service Accounts** → **Create**
   - Asigna rol: **Project → Editor**
   - **Keys** → **Add Key** → **JSON**
5. Descarga el archivo JSON
6. Guarda en `credentials/google-cloud-key.json`
7. Actualiza `.env`:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=credentials/google-cloud-key.json
   ```

#### Opción B: Sin APIs reales (Demo simulado)

Si no quieres configurar Google Cloud, el agente de voz funciona en modo simulación (sin audio real pero con arquitectura completa).

### 4. Base de Conocimiento (FAQs)

El archivo `data/faqs.json` contiene las preguntas frecuentes. Puedes personalizarlo:

```json
[
  {
    "id": 1,
    "category": "horarios",
    "question": "¿Cuál es el horario de atención?",
    "answer": "Nuestros horarios son: Lunes a Viernes 8:00 AM - 5:00 PM..."
  }
]
```

---

## 🚀 Uso

### Modo 1: Línea de Comandos (Interactivo)

```bash
python main.py
```

**Interfaz:**

```
======================================================================
🏦 AGENTE BANCARIO - BANCO NACIONAL DEL ECUADOR
======================================================================

Escribe tu mensaje (o 'salir' para terminar):
> Hola

Agente: ¡Hola! 👋 Soy tu asistente virtual...

> ¿Cuál es mi saldo?

Agente: Para consultarlo, necesito verificar tu identidad...
```

**Comandos especiales:**
- `salir` o `exit`: Terminar sesión
- `clear`: Limpiar pantalla
- `help`: Mostrar ayuda

### Modo 2: Demo de Voz

```bash
python voice_demo.py
```

**Opciones:**

```
======================================================================
DEMOS DISPONIBLES:
======================================================================
1. Generación de Voz (TTS)
2. Integración con Agente Bancario
3. Arquitectura del Sistema
4. Estadísticas
5. Ejecutar todos los demos
0. Salir
======================================================================

Selecciona: 1
```

**Resultado:** Genera archivos MP3 con audio real (si tienes Google Cloud configurado).

### Modo 3: API REST (Opcional)

```bash
# Iniciar servidor
python api.py

# En otra terminal, hacer request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¿Cuál es el horario de atención?",
    "session_id": "user-123"
  }'
```

**Respuesta:**

```json
{
  "response": "Nuestros horarios son: Lunes a Viernes...",
  "session_id": "user-123",
  "timestamp": "2025-10-12T10:30:00Z"
}
```

**Documentación interactiva:** http://localhost:8000/docs

---

## 🏗️ Arquitectura

### Diagrama General

```
┌──────────────┐
│   Usuario    │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│       BankingAgent (Orquestador)     │
│  • Gestión de conversación           │
│  • Control de sesión                 │
│  • Validación de seguridad           │
└────┬─────────────┬──────────┬────────┘
     │             │          │
     ↓             ↓          ↓
┌─────────┐  ┌─────────┐  ┌──────────┐
│ Gemini  │  │   RAG   │  │  Tools   │
│  2.5    │  │ +Vector │  │ (6 APIs) │
│ Flash   │  │   DB    │  │          │
└─────────┘  └─────────┘  └──────────┘
```

### Componentes Principales

| Componente | Archivo | Descripción |
|------------|---------|-------------|
| **Agente Principal** | `src/agent.py` | Orquestador de la conversación |
| **Tools Manager** | `src/tools.py` | Gestión de herramientas/APIs |
| **Knowledge Base** | `src/knowledge.py` | Sistema RAG con embeddings |
| **Security** | `src/security.py` | Validación y rate limiting |
| **Voice Agent** | `src/voice_agent.py` | Extensión para voz |
| **Configuración** | `config/settings.py` | Variables globales |
| **Prompts** | `config/prompts.py` | System prompts |

### Flujo de Datos

```python
1. Usuario → Input
2. SecurityManager → Validación
3. BankingAgent → Análisis con Gemini
4. ¿Necesita tool? 
   → Sí: Ejecutar tool → Respuesta
   → No: RAG search → Contexto
5. Gemini → Genera respuesta
6. SecurityManager → Sanitización
7. Logging → Guardar métrica
8. Usuario ← Output
```

---

## 📚 Documentación

### Documentos Técnicos

El proyecto incluye 3 documentos completos en `docs/`:

1. **`final_report.md`** (35 páginas)
   - Respuestas a todas las preguntas del caso
   - Justificación de decisiones técnicas
   - KPIs y métricas

2. **`technical_document.md`** (25 páginas)
   - Arquitectura detallada
   - Guías de implementación
   - Testing y deployment

3. **`voice_agent_extension.md`** (30 páginas)
   - Diseño del agente de voz
   - Análisis de costos
   - Roadmap de implementación

### Código Documentado

Cada módulo incluye:
- Docstrings en español
- Type hints
- Comentarios explicativos
- Ejemplos de uso

```python
def authenticate_user(document_id: str, otp_code: str) -> Dict:
    """
    Autentica un usuario usando 2FA.
    
    Args:
        document_id: Número de cédula del usuario
        otp_code: Código OTP de 6 dígitos
        
    Returns:
        Dict con éxito/fallo y datos de sesión
        
    Example:
        >>> result = authenticate_user("1234567890", "123456")
        >>> print(result['success'])
        True
    """
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html

# Tests específicos
pytest tests/test_agent.py -v
pytest tests/test_rag.py -v
pytest tests/test_tools.py -v
```

### Estructura de Tests

```
tests/
├── test_agent.py       # Tests del agente principal
├── test_rag.py         # Tests del sistema RAG
├── test_tools.py       # Tests de herramientas
├── test_security.py    # Tests de seguridad
└── test_voice.py       # Tests del agente de voz
```

### Ejemplos de Tests

```python
# Test de FAQ
def test_faq_response(agent):
    response = agent.process_message("¿Cuál es el horario?")
    assert "8:00" in response.lower()

# Test de autenticación
def test_auth_required(agent):
    response = agent.process_message("¿Cuál es mi saldo?")
    assert "autenticación" in response.lower()
```

### Coverage Report

```bash
pytest --cov=src --cov-report=html
# Abrir: htmlcov/index.html
```

**Target de cobertura:** >80%

---

## 🐛 Troubleshooting

### Problema 1: "ModuleNotFoundError: No module named 'google.generativeai'"

**Causa:** Dependencias no instaladas

**Solución:**
```bash
pip install -r requirements.txt
```

### Problema 2: "Error: GEMINI_API_KEY not found"

**Causa:** Variable de entorno no configurada

**Solución:**
```bash
# Verificar .env
cat .env | grep GEMINI_API_KEY

# Si está vacío, agregar:
echo "GEMINI_API_KEY=tu_api_key" >> .env
```

### Problema 3: "ChromaDB collection not found"

**Causa:** Base de conocimiento no indexada

**Solución:**
```bash
python -c "from src.knowledge import KnowledgeBase; kb = KnowledgeBase(); print('✅ Indexación completa')"
```

### Problema 4: Voice Agent - "API key not valid"

**Causa:** Usando API Key simple en vez de Service Account

**Soluciones:**
- **Opción A:** Configurar Service Account (ver sección Configuración)
- **Opción B:** Usar modo simulado (funciona sin configuración adicional)

### Problema 5: Latencia alta (>5 segundos)

**Diagnóstico:**
```bash
tail -f logs/agent.log
```

**Posibles causas:**
- Internet lento → Usar caché
- Gemini API slow → Verificar status en https://status.cloud.google.com/
- RAG search lento → Reducir tamaño de base de conocimiento

### Problema 6: "Permission denied" al ejecutar

**Linux/macOS:**
```bash
chmod +x main.py voice_demo.py
```

**Windows:**
```bash
# Ejecutar como:
python main.py
# En vez de:
./main.py
```

### Logs y Debugging

```bash
# Ver logs en tiempo real
tail -f logs/agent.log

# Buscar errores
grep "ERROR" logs/agent.log

# Logs con más detalle
export LOG_LEVEL=DEBUG
python main.py
```

---

## 📁 Estructura del Proyecto

```
banking-ai-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py              # Agente principal
│   ├── tools.py              # 6 herramientas funcionales
│   ├── knowledge.py          # Sistema RAG + ChromaDB
│   ├── security.py           # Validación y seguridad
│   └── voice_agent.py        # Agente de voz (Caso #2)
│
├── config/
│   ├── settings.py           # Configuración global
│   └── prompts.py            # System prompts
│
├── data/
│   └── faqs.json            # Base de conocimiento (FAQs)
│
├── tests/
│   ├── test_agent.py
│   ├── test_rag.py
│   ├── test_tools.py
│   ├── test_security.py
│   └── test_voice.py
│
├── docs/
│   ├── final_report.md              # Informe completo
│   ├── technical_document.md        # Documentación técnica
│   └── voice_agent_extension.md     # Caso #2
│
├── credentials/              # Ignorado por git
│   └── .gitkeep
│
├── logs/                     # Ignorado por git
│   └── .gitkeep
│
├── main.py                   # CLI principal (Caso #1)
├── voice_demo.py            # Demo de voz (Caso #2)
├── api.py                   # API REST (opcional)
│
├── requirements.txt         # Dependencias
├── .env.example            # Template de configuración
├── .gitignore
├── README.md               # Este archivo
├── Dockerfile              # Docker config
└── pytest.ini              # Configuración de tests
```

---

## 🐳 Docker (Opcional)

### Build

```bash
docker build -t banking-ai-agent .
```

### Run

```bash
docker run -it --env-file .env banking-ai-agent
```

### Docker Compose

```yaml
version: '3.8'
services:
  agent:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

---

## 🔐 Seguridad

### Buenas Prácticas Implementadas

- ✅ **Nunca** commitear API keys
- ✅ **Validación de input** (XSS, SQL injection)
- ✅ **Rate limiting** (30 requests/min)
- ✅ **2FA** para consultas sensibles
- ✅ **Output sanitization** (enmascarar datos)
- ✅ **Session management** con timeout
- ✅ **Logging de eventos de seguridad**

### Archivo `.gitignore`

```gitignore
# Credenciales
.env
credentials/
*.json

# API keys
*_key.json
*apikey*

# Logs
logs/
*.log

# Archivos de audio
*.mp3
*.wav

# Python
__pycache__/
*.pyc
venv/
.pytest_cache/

# IDE
.vscode/
.idea/
```

---

## 📊 Métricas y Monitoreo

### KPIs Implementados

| Métrica | Descripción | Target |
|---------|-------------|--------|
| **Resolution Rate** | % consultas resueltas sin humano | >75% |
| **CSAT** | Satisfacción del cliente | >85% |
| **Latency (p95)** | Tiempo de respuesta | <2s |
| **Intent Accuracy** | Detección correcta de intención | >90% |
| **Escalation Rate** | % derivado a humano | <20% |

### Logs Capturados

```python
{
    "conversation_id": "conv-123",
    "timestamp": "2025-10-12T10:30:00Z",
    "user_message": "¿cuál es mi saldo?",
    "agent_response": "Para consultarlo...",
    "intent": "check_balance",
    "tools_used": ["authenticate_user"],
    "latency_ms": 1850,
    "success": true
}
```

---

## 🤝 Contribuir

### Cómo Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código

- **Estilo:** PEP 8 (usar `black` formatter)
- **Type hints:** Obligatorios en funciones públicas
- **Docstrings:** En español, formato Google
- **Tests:** Cobertura >80% para nuevo código

```bash
# Formatear código
black src/ tests/

# Linting
pylint src/

# Type checking
mypy src/
```

---

## 🎓 Recursos Adicionales

### Documentación de APIs Usadas

- **Gemini API:** https://ai.google.dev/docs
- **Google Cloud TTS:** https://cloud.google.com/text-to-speech/docs
- **Google Cloud STT:** https://cloud.google.com/speech-to-text/docs
- **ChromaDB:** https://docs.trychroma.com/

### Tutoriales

- **Prompt Engineering:** https://ai.google.dev/docs/prompt_best_practices
- **Function Calling:** https://ai.google.dev/docs/function_calling
- **RAG con LangChain:** https://python.langchain.com/docs/use_cases/question_answering/

### Papers de Referencia

- **RAG:** "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- **Tool Use:** "Toolformer: Language Models Can Teach Themselves to Use Tools"

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

```
MIT License

Copyright (c) 2025 Carlos Israel Jiménez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 👤 Autor

**Carlos Israel Jiménez**

- GitHub: [@carlos-israelj](https://github.com/carlos-israelj)
- LinkedIn: [Carlos Jiménez](https://linkedin.com/in/carlos-jimenez)
- Email: carlos.jimenez@example.com

---

## 🙏 Agradecimientos

- **Google AI Studio** por proporcionar acceso a Gemini API
- **Anthropic** por inspiración en arquitecturas conversacionales
- **OpenAI** por avances en function calling
- **Comunidad open source** por las herramientas utilizadas

---

## 📈 Roadmap

### Version 1.0 (Actual)
- ✅ Agente conversacional básico
- ✅ 6 tools funcionales
- ✅ RAG con FAQs
- ✅ Seguridad básica
- ✅ Agente de voz (TTS funcional)

### Version 1.1 (Próximo mes)
- [ ] Fine-tuning con datos reales
- [ ] Análisis de sentimiento
- [ ] Detección de intención mejorada
- [ ] Dashboard de métricas

### Version 2.0 (3-6 meses)
- [ ] Multi-idioma (inglés, portugués)
- [ ] Integración con WhatsApp Business
- [ ] Agente de voz completo con STT
- [ ] Recomendaciones personalizadas
- [ ] Detección proactiva de fraude

---

## ❓ FAQ

### ¿Cuánto cuesta ejecutar el agente?

**Por conversación típica (5 mensajes):**
- Gemini API: ~$0.001
- ChromaDB: $0 (local)
- Total: **<$0.01 por conversación**

### ¿Funciona offline?

No. Requiere conexión a internet para:
- Gemini API
- Google Cloud TTS/STT (si usa voz)

Sin embargo, ChromaDB funciona localmente.

### ¿Puedo usar otro LLM?

Sí. El código está diseñado para ser agnóstico del modelo. Puedes reemplazar Gemini por:
- GPT-4 / GPT-3.5
- Claude (Anthropic)
- Llama 2 / Mistral (local)

### ¿Es escalable?

Sí. Diseñado para:
- Horizontal scaling (múltiples instancias)
- Load balancing
- Stateless (session en DB externa)

Para >1000 usuarios concurrentes, considera:
- Deploy en Kubernetes
- Redis para sesiones
- PostgreSQL para logs

### ¿Qué tan seguro es?

Implementa:
- Validación de input/output
- Rate limiting
- 2FA para operaciones sensibles
- Logging de seguridad
- Enmascaramiento de datos

**No** reemplaza un pentest profesional.

---

## 📞 Soporte

¿Problemas? ¿Preguntas?

1. **GitHub Issues:** https://github.com/carlos-israelj/banking-ai-agent/issues
2. **Email:** soporte@ejemplo.com
3. **Documentación:** Ver carpeta `docs/`

**Tiempo de respuesta:** 24-48 horas

---

## ⭐ ¿Te gustó el proyecto?

Si este proyecto te fue útil:

1. Dale una ⭐ en GitHub
2. Compártelo con tu equipo
3. Contribuye con mejoras
4. Reporta bugs

**¡Gracias por usar Banking AI Agent!** 🚀

---

*Última actualización: Octubre 2025*  
*Versión: 1.0.0*