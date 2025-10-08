"""
Configuración global del sistema.
"""
import os

# Intentar cargar dotenv, pero no fallar si no existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# API Keys - SIEMPRE con valor por defecto
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyCWM_Zl7KJKhz0mIfzmSO7y9o-_mZ8yNFI')

# Configuración del modelo
MODEL_NAME = os.environ.get('MODEL_NAME', 'gemini-2.5-flash')
MODEL_TEMPERATURE = float(os.environ.get('MODEL_TEMPERATURE', '0.7'))
MODEL_MAX_TOKENS = int(os.environ.get('MODEL_MAX_TOKENS', '2048'))

# Configuración de seguridad
SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT_MINUTES', '15'))
MAX_FAILED_AUTH_ATTEMPTS = int(os.environ.get('MAX_FAILED_AUTH_ATTEMPTS', '3'))
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '30'))
RATE_LIMIT_WINDOW_MINUTES = int(os.environ.get('RATE_LIMIT_WINDOW_MINUTES', '1'))

# Configuración de la aplicación
MAX_CONVERSATION_HISTORY = int(os.environ.get('MAX_CONVERSATION_HISTORY', '50'))
ENABLE_LOGGING = os.environ.get('ENABLE_LOGGING', 'true').lower() == 'true'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Rutas de archivos
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
FAQS_FILE = os.path.join(DATA_DIR, 'faqs.json')

# Configuración de RAG
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'paraphrase-multilingual-mpnet-base-v2')
TOP_K_RESULTS = int(os.environ.get('TOP_K_RESULTS', '3'))
SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', '0.5'))

# Mensajes del sistema
WELCOME_MESSAGE = """¡Hola! 👋 Soy tu asistente virtual bancario.

Puedo ayudarte con:
- Consultas sobre productos y servicios
- Información de tus cuentas y tarjetas (requiere autenticación)
- Preguntas sobre pólizas de seguro

¿En qué puedo ayudarte hoy?"""

GOODBYE_MESSAGE = "¡Gracias por usar nuestro servicio! Que tengas un excelente día. 👋"

ERROR_MESSAGE = "Disculpa, tuve un problema al procesar tu solicitud. ¿Puedes intentar de nuevo o reformular tu pregunta?"

AUTH_REQUIRED_MESSAGE = "Por tu seguridad, necesito verificar tu identidad primero. ¿Tienes a mano tu documento de identidad? 🔐"

# Configuración de herramientas
TOOL_TIMEOUT_SECONDS = int(os.environ.get('TOOL_TIMEOUT_SECONDS', '5'))
TOOL_RETRY_ATTEMPTS = int(os.environ.get('TOOL_RETRY_ATTEMPTS', '2'))

# Banco de prueba (datos simulados)
BANK_INFO = {
    "name": "Banco Nacional del Ecuador",
    "support_phone": "1-800-BANCO-24",
    "support_email": "ayuda@banconacional.com.ec",
    "website": "www.banconacional.com.ec",
    "hours": {
        "weekdays": "Lunes a Viernes: 8:00 AM - 5:00 PM",
        "saturday": "Sábados: 9:00 AM - 1:00 PM",
        "sunday": "Cerrado"
    }
}

# Validación de configuración
def validate_config():
    """Valida que la configuración esté correcta"""
    errors = []
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'tu_api_key_aqui':
        errors.append("GEMINI_API_KEY no está configurada correctamente")
    
    if SESSION_TIMEOUT_MINUTES < 1:
        errors.append("SESSION_TIMEOUT_MINUTES debe ser mayor a 0")
    
    if RATE_LIMIT_REQUESTS < 1:
        errors.append("RATE_LIMIT_REQUESTS debe ser mayor a 0")
    
    if errors:
        print(f"⚠️  Advertencias de configuración: {', '.join(errors)}")
    
    return True

# Validar al importar
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  Advertencia de configuración: {e}")