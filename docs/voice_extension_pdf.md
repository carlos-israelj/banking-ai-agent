# Extensión del Caso: Agente de Voz en Tiempo Real

**Caso de Evaluación: AI Engineer - Caso #2 (Opcional)**  
**Autor:** Carlos Israel Jiménez  
**Fecha:** Octubre 2025

---

## Tabla de Contenidos

1. [Contexto y Objetivos](#contexto-y-objetivos)
2. [Arquitectura para Llamadas en Tiempo Real](#arquitectura-para-llamadas-en-tiempo-real)
3. [Flujo Conversacional para Voz](#flujo-conversacional-para-voz)
4. [Manejo de Errores y Fallback](#manejo-de-errores-y-fallback)
5. [Implementación Técnica](#implementación-técnica)
6. [Análisis de Costos](#análisis-de-costos)
7. [Resultados y Próximos Pasos](#resultados-y-próximos-pasos)

---

## Contexto y Objetivos

### Necesidad del Negocio

El Banco Nacional busca evolucionar su canal telefónico de atención al cliente, reemplazando los sistemas IVR tradicionales con menús de opciones por un agente conversacional inteligente que:

- Comprende lenguaje natural
- Mantiene conversaciones fluidas
- Accede a la misma información que el agente de WhatsApp
- Reduce tiempos de espera
- Mejora satisfacción del cliente

### Alcance del Caso #2

Este documento presenta:
1. **Diseño arquitectónico completo** del sistema de voz
2. **Implementación parcial funcional** (TTS + integración con agente base)
3. **Arquitectura lista para producción** (STT + telefonía)
4. **Análisis técnico y económico** de la solución

---

## Arquitectura para Llamadas en Tiempo Real

### 7.1 Componentes del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                  USUARIO (Teléfono)                     │
│           Habla en lenguaje natural                     │
└────────────────────┬────────────────────────────────────┘
                     │ Audio analógico
                     ↓
┌─────────────────────────────────────────────────────────┐
│        TWILIO / VONAGE (Telefonía Cloud)                │
│  • Recepción de llamadas entrantes                      │
│  • Conversión a digital (PCM)                           │
│  • WebSocket bidireccional en tiempo real               │
│  • Gestión de sesiones telefónicas                      │
└────────────────────┬────────────────────────────────────┘
                     │ Audio digital (PCM)
                     ↓
┌─────────────────────────────────────────────────────────┐
│         VOICE ACTIVITY DETECTION (VAD)                  │
│  • Detecta cuándo el usuario empieza/termina de hablar │
│  • Filtra ruido de fondo y silencio                     │
│  • Permite interrupciones (barge-in)                    │
│  • End-of-speech detection                              │
└────────────────────┬────────────────────────────────────┘
                     │ Segmentos de audio
                     ↓
┌─────────────────────────────────────────────────────────┐
│    GOOGLE CLOUD SPEECH-TO-TEXT (STT)                    │
│  • Modelo: default / phone_call                         │
│  • Idioma: es-EC (Español Ecuador)                      │
│  • Streaming mode: Real-time                            │
│  • Automatic punctuation: Enabled                       │
│  • Latencia: ~300-500ms                                 │
└────────────────────┬────────────────────────────────────┘
                     │ Texto transcrito
                     ↓
┌─────────────────────────────────────────────────────────┐
│       BANKING AGENT CORE (Caso #1 - Reutilizado)        │
│  • Gemini 2.5 Flash                                     │
│  • Tool calling (6 herramientas)                        │
│  • RAG para FAQs                                        │
│  • Gestión de sesión y autenticación                    │
│  • Latencia: ~1-2s                                      │
└────────────────────┬────────────────────────────────────┘
                     │ Respuesta en texto
                     ↓
┌─────────────────────────────────────────────────────────┐
│    GOOGLE CLOUD TEXT-TO-SPEECH (TTS)                    │
│  • Modelo: es-ES-Standard-A / Wavenet / Neural2         │
│  • Voz: Femenina natural                                │
│  • Speaking rate: Configurable (0.85x - 1.15x)          │
│  • SSML support para énfasis y pausas                   │
│  • Latencia: ~200-400ms                                 │
│  ✅ COMPONENTE IMPLEMENTADO Y FUNCIONAL                 │
└────────────────────┬────────────────────────────────────┘
                     │ Audio MP3
                     ↓
┌─────────────────────────────────────────────────────────┐
│         AUDIO STREAMING → Usuario                       │
│  • Reproducción mientras se genera                      │
│  • Buffer mínimo para fluidez                           │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Interacción de Componentes

**Secuencia de una interacción completa:**

```
T0: Usuario marca número del banco
    ↓
T1: Twilio recibe llamada y abre WebSocket
    ↓
T2: Agente reproduce saludo (TTS pre-generado)
    "Hola, Banco Nacional. ¿En qué puedo ayudarte?"
    ↓
T3: Usuario habla: "Quiero saber mi saldo"
    ↓
T4: VAD detecta fin de habla (end-of-speech)
    ↓
T5: STT transcribe: "quiero saber mi saldo"
    Latencia: ~500ms
    ↓
T6: BankingAgent procesa:
    - Detecta intención: check_balance
    - Verifica autenticación: NO
    - Genera respuesta: "Para consultarlo, necesito tu cédula"
    Latencia: ~1.5s
    ↓
T7: TTS sintetiza respuesta a audio
    Latencia: ~300ms
    ↓
T8: Audio se reproduce al usuario vía Twilio
    ↓
T9: Usuario responde con su cédula...
    [Loop continúa]
```

**Latencia total por turno:** ~2.3 segundos

---

### 7.3 Garantizar Baja Latencia

**Objetivo:** <3 segundos end-to-end para mantener conversación fluida

#### **Estrategias de Optimización:**

**1. Streaming STT/TTS**
```python
# En vez de esperar frase completa:
# ANTES: "Hola cómo estás" [ESPERA] [PROCESA TODO]
# AHORA: "Hola" [PROCESA] "cómo" [PROCESA] "estás" [PROCESA]

# Beneficio: Reduce latencia percibida a la mitad
```

**2. Caché de Frases Comunes**
```python
CACHED_AUDIO = {
    "greeting": "greeting.mp3",  # "Hola, Banco Nacional"
    "auth_request": "auth.mp3",  # "Por tu seguridad..."
    "goodbye": "goodbye.mp3",     # "Que tengas buen día"
}

# Audio pre-generado con máxima calidad
# Reproducción instantánea (~0ms latency)
```

**3. Predicción de Intención**
```python
# Mientras el usuario habla, predecir posible intención
# Si confianza > 80%, pre-generar respuesta probable

if predicted_intent == "check_balance" and confidence > 0.8:
    pre_generate_tts("Para consultarlo, necesito tu cédula")
    # Si la predicción es correcta, respuesta instantánea
```

**4. Parallel Processing**
```python
# Ejecutar operaciones independientes en paralelo
async def process_user_input(audio):
    # Paralelo:
    transcription, user_profile = await asyncio.gather(
        stt.transcribe(audio),
        db.get_user_profile(phone_number)
    )
    # Reduce latencia total
```

**5. Edge Deployment**
```
Usuario (Ecuador) → Servidor en São Paulo (AWS SA-EAST-1)
# vs
Usuario (Ecuador) → Servidor en Virginia (US-EAST-1)

Latencia de red: 30ms vs 150ms
Ahorro: 120ms por round-trip
```

---

## Flujo Conversacional para Voz

### 8.1 Diferencias Clave vs WhatsApp

| Aspecto | WhatsApp (Texto) | Voz (Llamada) |
|---------|------------------|---------------|
| **Canal de comunicación** | Asíncrono | Síncrono |
| **Ritmo** | Usuario lee a su ritmo | Tiempo real, sin pausa |
| **Interrupciones** | No aplica | Usuario puede interrumpir |
| **Correcciones** | Editar mensaje | Pedir repetición verbal |
| **Confirmación** | Visual (✓✓) | Verbal explícita |
| **Números/URLs largos** | Fácil copiar | Difícil recordar → SMS |
| **Información densa** | OK, usuario relee | Resumir, hablar despacio |
| **Multitarea** | Sí (cocinar, caminar) | Requiere atención |
| **Registro permanente** | Sí, queda escrito | No, salvo que se grabe |
| **Expresión** | Emojis, negritas | Tono, velocidad, pausas |

---

### 8.2 Adaptaciones Implementadas

#### **A) Manejo de Interrupciones (Barge-in)**

**Problema:** Usuario interrumpe mientras el agente habla

**Solución:**

```python
class VoiceConversationManager:
    def __init__(self):
        self.is_speaking = False
        self.current_audio_stream = None
    
    def on_user_speech_detected(self):
        """
        VAD detecta que el usuario empezó a hablar
        """
        if self.is_speaking:
            # Detener inmediatamente reproducción actual
            self.stop_current_playback()
            self.is_speaking = False
            
            # Preparar para escuchar
            self.start_listening()
            
            logger.info("Barge-in detected: User interrupted agent")
    
    def stop_current_playback(self):
        """Detiene audio en curso"""
        if self.current_audio_stream:
            self.current_audio_stream.cancel()
            self.current_audio_stream = None
```

**Resultado:** Conversación natural donde el usuario puede interrumpir sin esperar.

---

#### **B) Confirmaciones Verbales Explícitas**

**En texto:**
```
Usuario: ¿Cuál es mi saldo?
Agente: $5,420.50
```

**En voz:**
```
Usuario: ¿Cuál es mi saldo?
Agente: Perfecto, Carlos. Tu saldo disponible en la 
        cuenta de ahorros es cinco mil cuatrocientos 
        veinte dólares con cincuenta centavos.
        
        ¿Hay algo más en lo que pueda ayudarte?
```

**Razones:**
- Dar tiempo al usuario para anotar
- Confirmar comprensión mutua
- Evitar ambigüedades ($5,420 vs $5,020)

---

#### **C) Manejo de Números Largos**

**Problema:** Números de cuenta (16 dígitos) son difíciles de dictar/recordar

**Solución:**

```python
def format_for_voice(self, data, data_type):
    """Adapta información para comunicación verbal"""
    
    if data_type == "account_number":
        # NO dictar 16 dígitos
        # EN LUGAR:
        return "Te envié el número completo por SMS"
        self.send_sms(user_phone, account_number)
    
    elif data_type == "amount":
        # $5,420.50 → "cinco mil cuatrocientos veinte 
        #              dólares con cincuenta centavos"
        return self.number_to_words(amount, currency="USD")
    
    elif data_type == "date":
        # 2025-10-15 → "quince de octubre de dos mil veinticinco"
        return self.date_to_natural_speech(date)
    
    elif data_type == "url":
        # https://banco.com/app/download
        # → "Te envié el link por SMS"
        return "Te envié el enlace de descarga por mensaje"
        self.send_sms(user_phone, url)
```

---

#### **D) Velocidad de Habla Adaptativa**

**Problema:** Algunos usuarios prefieren ritmo más lento/rápido

**Solución:**

```python
class AdaptiveTTSManager:
    def __init__(self):
        self.default_speed = 1.0
        self.user_preferences = {}  # user_id: speed
    
    def process_speed_command(self, user_id, utterance):
        """Detecta y aplica cambios de velocidad"""
        
        if "más despacio" in utterance or "lento" in utterance:
            self.user_preferences[user_id] = 0.85
            return "Entendido, voy a hablar más despacio"
        
        elif "más rápido" in utterance or "rápido" in utterance:
            self.user_preferences[user_id] = 1.15
            return "De acuerdo, aumentaré la velocidad"
        
        elif "velocidad normal" in utterance:
            self.user_preferences[user_id] = 1.0
            return "Perfecto, velocidad normal"
    
    def get_speed_for_user(self, user_id):
        """Obtiene velocidad preferida del usuario"""
        return self.user_preferences.get(user_id, self.default_speed)
```

---

#### **E) Pausas y Énfasis con SSML**

```python
def add_emphasis_for_voice(self, text, context):
    """Agrega pausas y énfasis usando SSML"""
    
    if context == "important_security":
        # Enfatizar información de seguridad
        return f"""
        <speak>
            <emphasis level="strong">Por tu seguridad</emphasis>,
            <break time="500ms"/>
            necesito verificar tu identidad.
        </speak>
        """
    
    elif context == "list_items":
        # Pausas entre elementos de lista
        items = text.split(',')
        ssml_items = '<break time="300ms"/>'.join(items)
        return f"<speak>{ssml_items}</speak>"
```

---

### 8.3 Manejo de Ruido Ambiental

**Desafíos:**
- Usuario llama desde calle ruidosa
- Ruido de fondo (niños, TV, tráfico)
- Mala señal telefónica

**Estrategia Multinivel:**

```python
class AudioQualityManager:
    def __init__(self):
        self.low_confidence_count = 0
        self.max_retries = 3
    
    def handle_transcription(self, result):
        """Maneja transcripción con validación de calidad"""
        
        confidence = result['confidence']
        
        if confidence < 0.70:
            # Confianza baja - Probablemente ruido
            self.low_confidence_count += 1
            
            if self.low_confidence_count == 1:
                # Primer intento: Pedir repetición educadamente
                return "Disculpa, no pude escucharte bien. ¿Podrías repetir?"
            
            elif self.low_confidence_count == 2:
                # Segundo intento: Sugerir mejor ubicación
                return "Parece que hay mucho ruido de fondo. ¿Puedes moverte a un lugar más tranquilo?"
            
            else:
                # Tercer intento: Ofrecer alternativas
                return """No logro escucharte claramente. ¿Prefieres que:
                          1. Te llame de vuelta en unos minutos, o
                          2. Te envíe un mensaje por WhatsApp?"""
        
        else:
            # Confianza buena - Resetear contador
            self.low_confidence_count = 0
            return result['text']
```

**Tecnologías Adicionales:**
- **Noise suppression** en Twilio (Krisp.ai integration)
- **STT model:** `phone_call` (optimizado para telefonía)
- **Audio filters:** High-pass filter para ruido de fondo

---

### 8.4 Tools Adicionales para Voz

Además de las 6 tools del Caso #1, el agente de voz incluye:

#### **Tool 7: send_sms**

```python
def send_sms(phone_number: str, message: str) -> Dict:
    """
    Envía SMS con información difícil de comunicar verbalmente.
    
    Casos de uso:
    - Números de cuenta largos
    - URLs para apps
    - Códigos de confirmación
    - Resumen de la conversación
    
    Args:
        phone_number: Número del usuario (extraído de Twilio)
        message: Contenido del SMS
    
    Returns:
        {
            "success": bool,
            "message_sid": str,  # ID del mensaje en Twilio
            "status": str        # "queued" | "sent" | "delivered"
        }
    """
    try:
        from twilio.rest import Client
        
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status
        }
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        return {"success": False, "error": str(e)}
```

---

#### **Tool 8: schedule_callback**

```python
def schedule_callback(user_id: str, phone_number: str, preferred_time: str) -> Dict:
    """
    Programa una llamada de retorno con asesor humano.
    
    Usado cuando:
    - Consulta muy compleja para agente IA
    - Usuario solicita hablar con humano explícitamente
    - Temas sensibles (fraude, disputa, fallecimiento)
    
    Args:
        user_id: ID del usuario
        phone_number: Número para callback
        preferred_time: "now" | "1 hour" | "tomorrow 10am" | etc.
    
    Returns:
        {
            "success": bool,
            "callback_id": str,
            "scheduled_time": str (ISO format)
        }
    """
    # Integración con sistema de gestión de llamadas del banco
    callback_time = parse_time_preference(preferred_time)
    
    callback_id = create_callback_task(
        user_id=user_id,
        phone=phone_number,
        scheduled_for=callback_time,
        reason="user_request"
    )
    
    return {
        "success": True,
        "callback_id": callback_id,
        "scheduled_time": callback_time.isoformat()
    }
```

---

#### **Tool 9: adjust_voice_settings**

```python
def adjust_voice_settings(setting: str, value: float) -> Dict:
    """
    Ajusta parámetros de la voz del agente en tiempo real.
    
    Parámetros:
    - speed: 0.75 (lento) - 1.25 (rápido)
    - pitch: 0.9 (grave) - 1.1 (agudo)
    - volume: 0.8 (bajo) - 1.2 (alto)
    
    Ejemplos:
    - Usuario: "Habla más despacio" → speed=0.85
    - Usuario: "No te escucho bien" → volume=1.1
    """
    valid_settings = {
        "speed": (0.75, 1.25),
        "pitch": (0.9, 1.1),
        "volume": (0.8, 1.2)
    }
    
    if setting not in valid_settings:
        return {"success": False, "error": "INVALID_SETTING"}
    
    min_val, max_val = valid_settings[setting]
    if not (min_val <= value <= max_val):
        return {"success": False, "error": "VALUE_OUT_OF_RANGE"}
    
    # Aplicar configuración
    self.tts_config[setting] = value
    
    return {
        "success": True,
        "setting": setting,
        "value": value
    }
```

---

## Manejo de Errores y Fallback

### 9.1 Estrategia de Recuperación en 3 Niveles

```
Usuario dice algo incomprensible
    ↓
┌────────────────────────────────────────────┐
│ NIVEL 1: Retry Amable                      │
│ "Disculpa, no pude escucharte bien.        │
│  ¿Podrías repetir?"                        │
│                                            │
│ • Se usa en primer error                   │
│ • Tono amable y no culpa al usuario        │
└────────────────┬───────────────────────────┘
                 │ Si persiste...
                 ↓
┌────────────────────────────────────────────┐
│ NIVEL 2: Ofrecer Alternativas             │
│ "No logro entenderte bien. ¿Prefieres:    │
│  1. Que te transfiera con un asesor       │
│  2. Enviarte un SMS para continuar por    │
│     WhatsApp?"                            │
│                                            │
│ • Da control al usuario                    │
│ • Ofrece canales alternativos              │
└────────────────┬───────────────────────────┘
                 │ Si sigue sin funcionar...
                 ↓
┌────────────────────────────────────────────┐
│ NIVEL 3: Escalamiento Automático          │
│ "Te voy a conectar con un asesor que      │
│  pueda ayudarte mejor. Un momento."       │
│                                            │
│ • Transferencia inmediata                  │
│ • Log de la situación                      │
│ • Asesor recibe contexto                   │
└────────────────────────────────────────────┘
```

---

### 9.2 Triggers de Escalamiento

| Situación | Tiempo de Espera | Acción |
|-----------|------------------|--------|
| 3 malentendidos seguidos | Inmediato | Ofrecer transferencia |
| Usuario dice "humano"/"asesor" | Inmediato | Transferir |
| Usuario dice "supervisor" | Inmediato | Transferir a supervisor |
| Consulta sobre fraude | Inmediato | Transferir a seguridad |
| Disputa de cargo | Inmediato | Transferir a disputas |
| Query fuera de alcance | 5 segundos | "Te conecto con especialista" |
| Error técnico (API caída) | Inmediato | "Problemas técnicos, transfering..." |

---

### 9.3 Manejo de Frases Especiales

```python
class MetaCommandHandler:
    """Maneja comandos meta-conversacionales"""
    
    COMMANDS = {
        # Repetición
        "repite": "repeat_last",
        "otra vez": "repeat_last",
        "no entendí": "repeat_slower",
        
        # Velocidad
        "más despacio": "slower",
        "más lento": "slower",
        "más rápido": "faster",
        
        # Clarificación
        "deletrea": "spell_out",
        "letra por letra": "spell_out",
        
        # Canales
        "por mensaje": "send_sms",
        "por whatsapp": "send_sms",
        "por correo": "send_email",
        
        # Escalamiento
        "con un humano": "transfer_human",
        "con una persona": "transfer_human",
        "con un asesor": "transfer_human",
    }
    
    def process(self, utterance: str) -> Optional[Action]:
        """Detecta y procesa comandos meta"""
        utterance_lower = utterance.lower()
        
        for trigger, action in self.COMMANDS.items():
            if trigger in utterance_lower:
                return self.execute_action(action)
        
        return None
    
    def execute_action(self, action: str):
        """Ejecuta la acción meta correspondiente"""
        
        if action == "repeat_last":
            return self.repeat_last_message(speed=1.0)
        
        elif action == "repeat_slower":
            return self.repeat_last_message(speed=0.85)
        
        elif action == "slower":
            self.adjust_speed(0.85)
            return self.repeat_last_message(speed=0.85)
        
        elif action == "faster":
            self.adjust_speed(1.15)
            return "Entendido, voy a hablar más rápido"
        
        elif action == "spell_out":
            last_entity = self.extract_last_entity()
            return self.spell_out_word(last_entity)
        
        elif action == "send_sms":
            last_info = self.get_last_important_info()
            self.send_sms_tool(last_info)
            return "Te acabo de enviar la información por SMS"
        
        elif action == "transfer_human":
            return self.initiate_transfer()
```

**Ejemplo de uso:**

```
Agente: Tu número de cuenta es cero cero cero uno dos tres cuatro...
Usuario: No entendí, por mensaje
Agente: [Detecta "por mensaje" → send_sms action]
        Te envié el número completo por SMS. ¿Algo más?
```

---

### 9.4 Manejo de Interrupciones de Conexión

```python
class ConnectionMonitor:
    def __init__(self):
        self.last_audio_received = None
        self.silence_threshold = 15  # segundos
        self.connection_lost_threshold = 30
    
    async def monitor_call(self):
        """Monitorea la conexión en tiempo real"""
        
        while self.call_active:
            now = datetime.now()
            silence_duration = (now - self.last_audio_received).seconds
            
            if silence_duration > self.silence_threshold:
                # Usuario no responde
                await self.speak("¿Sigues ahí? ¿Puedes escucharme?")
                await asyncio.sleep(5)
                
                if silence_duration > self.connection_lost_threshold:
                    # Probablemente se cayó la llamada
                    await self.speak(
                        "Parece que perdimos la conexión. "
                        "Llámanos de nuevo si necesitas ayuda. "
                        "Hasta luego."
                    )
                    self.end_call()
                    break
            
            await asyncio.sleep(1)
```

---

## Implementación Técnica

### 5.1 Stack Tecnológico

| Capa | Tecnología | Justificación | Status |
|------|------------|---------------|--------|
| **Telefonía** | Twilio | Líder del mercado, docs excelentes | 🔵 Diseñado |
| **STT** | Google Cloud Speech-to-Text | Mejor accuracy en español | 🔵 Arquitecturado |
| **VAD** | WebRTC VAD / Silero VAD | Open source, bajo latency | 🔵 Diseñado |
| **Agente** | BankingAgent (Caso #1) | Reutilización 100% | ✅ Funcional |
| **TTS** | Google Cloud Text-to-Speech | Voces naturales | ✅ Funcional |
| **Backend** | Python + FastAPI | Async, websockets | ✅ Funcional |

---

### 5.2 Código Implementado

#### **VoiceAgent - Componente TTS (Funcional)**

```python
# src/voice_agent.py

from google.cloud import texttospeech
from src.agent import BankingAgent

class VoiceAgent:
    """
    Agente de voz que integra TTS con el agente bancario base.
    
    Status: TTS completamente funcional con Google Cloud.
    """
    
    def __init__(self, gemini_api_key):
        # Reutilizar agente del Caso #1
        self.text_agent = BankingAgent(gemini_api_key)
        
        # Cliente TTS
        self.tts_client = texttospeech.TextToSpeechClient()
        
        # Configuración de voz
        self.voice_config = texttospeech.VoiceSelectionParams(
            language_code="es-ES",
            name="es-ES-Standard-A",  # Voz femenina
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
    
    def synthesize_speech(self, text, output_file="response.mp3"):
        """
        Genera audio real con Google Cloud TTS.
        
        FUNCIONAL: Genera archivos MP3 reales.
        """
        # Limpiar texto para voz
        clean_text = self._prepare_for_speech(text)
        
        # Crear input
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)
        
        # Sintetizar
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice_config,
            audio_config=self.audio_config
        )
        
        # Guardar MP3
        with open(output_file, 'wb') as out:
            out.write(response.audio_content)
        
        return {"success": True, "audio_file": output_file}
    
    def _prepare_for_speech(self, text):
        """Adapta texto para sonar natural en voz"""
        replacements = {
            "$": "dólares ",
            "USD": "dólares",
            "✅": "",
            "💳": ""
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
```

**Resultado:** Genera archivos MP3 reales con voz natural en español.

---

#### **Componente STT (Arquitecturado, listo para audio)**

```python
from google.cloud import speech

def transcribe_audio(audio_file_path):
    """
    Transcribe audio a texto con Google Cloud STT.
    
    STATUS: Código completo, listo para audio real.
    En el demo se simula el input por practicidad.
    """
    client = speech.SpeechClient()
    
    # Leer audio
    with open(audio_file_path, 'rb') as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=16000,
        language_code="es-ES",
        enable_automatic_punctuation=True,
        model="phone_call"  # Optimizado para llamadas
    )
    
    # Transcribir
    response = client.recognize(config=config, audio=audio)
    
    # Extraer texto
    transcript = response.results[0].alternatives[0].transcript
    confidence = response.results[0].alternatives[0].confidence
    
    return {
        "text": transcript,
        "confidence": confidence
    }
```

---

### 5.3 Flujo Completo (Producción)

```python
async def handle_call(call_sid):
    """
    Maneja una llamada telefónica completa.
    
    Este es el flujo que ocurriría en producción con Twilio.
    """
    # 1. Inicializar
    voice_agent = VoiceAgent(GEMINI_API_KEY)
    call = await twilio.get_call(call_sid)
    websocket = await call.open_websocket()
    
    # 2. Saludo inicial
    greeting = voice_agent.synthesize_speech(
        "Hola, Banco Nacional. ¿En qué puedo ayudarte?"
    )
    await websocket.send_audio(greeting)
    
    # 3. Loop de conversación
    while call.active:
        # 3a. Escuchar usuario
        audio_buffer = await websocket.receive_audio()
        
        # 3b. Detectar actividad de voz
        if vad.is_speech(audio_buffer):
            # 3c. Transcribir
            utterance = await stt.transcribe_streaming(audio_buffer)
            
            if vad.is_end_of_speech(audio_buffer):
                # Frase completa
                print(f"Usuario: {utterance}")
                
                # 3d. Procesar con agente
                response_text = voice_agent.text_agent.process_message(utterance)
                print(f"Agente: {response_text}")
                
                # 3e. Sintetizar respuesta
                audio_response = voice_agent.synthesize_speech(response_text)
                
                # 3f. Reproducir
                await websocket.send_audio(audio_response)
                
                # Reset buffer
                audio_buffer.clear()
    
    # 4. Finalizar
    await call.end()
```

---

## Análisis de Costos

### 6.1 Desglose de Costos por Llamada

**Llamada típica: 5 minutos**

| Servicio | Tarifa | Uso en 5 min | Costo |
|----------|--------|--------------|-------|
| **Twilio (llamada entrante)** | $0.013/min | 5 min | $0.065 |
| **Google Cloud STT** | $0.006/15s | 20 chunks | $0.12 |
| **Google Cloud TTS** | $4/1M chars | ~500 chars | $0.002 |
| **Compute (server)** | $0.10/hora | 0.083 horas | $0.008 |
| **Total** | | | **$0.195** |

**Redondeado:** ~**$0.20 por llamada**

---

### 6.2 Proyección de Costos Mensuales

| Volumen de Llamadas | Costo Mensual | Costo Anual |
|---------------------|---------------|-------------|
| 1,000 llamadas | $200 | $2,400 |
| 10,000 llamadas | $2,000 | $24,000 |
| 50,000 llamadas | $10,000 | $120,000 |
| 100,000 llamadas | $20,000 | $240,000 |

---

### 6.3 Comparación con Alternativas

| Opción | Costo/llamada | Pros | Contras |
|--------|---------------|------|---------|
| **Agente IA (nuestra solución)** | $0.20 | 24/7, escalable, consistente | Inicial inversión en desarrollo |
| **Agente humano** | $3-5 | Empatía máxima | Limitado a horarios, costoso |
| **IVR tradicional** | $0.05 | Muy barato | Mala UX, alta frustración |
| **Chatbot básico** | $0.10 | Barato | Sin voz, requiere app |

---

### 6.4 ROI Estimado

**Escenario: Banco mediano, 20,000 llamadas/mes**

**Situación actual (agentes humanos):**
- Costo por llamada: $4 (8 min * $30/hora)
- Costo mensual: 20,000 * $4 = **$80,000**

**Con agente IA:**
- Costo por llamada: $0.20
- Costo mensual: 20,000 * $0.20 = **$4,000**
- **Ahorro mensual: $76,000**
- **Ahorro anual: $912,000**

**Inversión inicial:** ~$30,000 (desarrollo + setup)
**Break-even:** <0.5 meses

---

## Resultados y Próximos Pasos

### 7.1 Estado Actual de Implementación

#### **✅ Completado:**

1. **Text-to-Speech Funcional**
   - Integración con Google Cloud TTS
   - Genera archivos MP3 reales
   - Voz natural en español
   - Configuración de velocidad/tono

2. **Integración con BankingAgent**
   - Reutilización 100% del agente del Caso #1
   - Sin modificaciones necesarias
   - Demuestra modularidad

3. **Documentación Completa**
   - Arquitectura detallada
   - Decisiones técnicas justificadas
   - Análisis de costos
   - Plan de implementación

#### **🔵 Arquitecturado (Listo para implementación):**

1. **Speech-to-Text**
   - Código completo
   - Configuración definida
   - Listo para audio real

2. **Telefonía (Twilio)**
   - WebSocket streaming diseñado
   - Flujo completo documentado

3. **Voice Activity Detection**
   - Selección de tecnología
   - Estrategia de implementación

---

### 7.2 Demo Ejecutable

**Archivo:** `voice_demo.py`

**Funcionalidad demostrada:**

```bash
$ python voice_demo.py

Opciones:
1. Generación de Voz (TTS) ✅
2. Integración con Agente Bancario ✅
3. Arquitectura del Sistema ✅
4. Estadísticas ✅

# Al seleccionar opción 1:
[Mensaje 1]
📝 Texto: ¡Hola! Bienvenido al Banco Nacional.
✅ Audio: demo_tts_1.mp3  # <- Archivo MP3 REAL generado
```

**Resultados:**
- Archivos MP3 reales con voz natural
- Integración funcional con BankingAgent
- Respuestas basadas en el agente del Caso #1

---

### 7.3 Próximos Pasos

#### **Fase 1: Prototipo Completo (2 semanas)**
- [ ] Implementar STT con audio real
- [ ] Integrar Twilio para llamadas de prueba
- [ ] Testing interno con equipo de QA

#### **Fase 2: Beta Testing (4 semanas)**
- [ ] Piloto con 100 clientes voluntarios
- [ ] Recolección de métricas
- [ ] Ajustes basados en feedback
- [ ] Fine-tuning de prompts si necesario

#### **Fase 3: Producción (8 semanas)**
- [ ] Deploy gradual (5% → 25% → 50% → 100% del tráfico)
- [ ] Monitoreo 24/7
- [ ] Team de soporte dedicado
- [ ] Documentación operacional completa

---

### 7.4 Métricas de Éxito

| KPI | Meta | Medición |
|-----|------|----------|
| **Call Completion Rate** | >80% | % de llamadas completadas sin escalamiento |
| **CSAT** | >4.0/5.0 | Encuesta post-llamada |
| **Average Handle Time** | <4 min | Duración promedio |
| **First Call Resolution** | >70% | % resuelto en primera llamada |
| **Escalation Rate** | <15% | % transferido a humano |

---

## Conclusión

### Resumen de Logros

**Caso #2 - Agente de Voz:**

1. ✅ **Arquitectura completa diseñada** con todos los componentes necesarios
2. ✅ **TTS completamente funcional** con Google Cloud (genera audio real)
3. ✅ **Integración con agente base** sin modificaciones
4. ✅ **Análisis técnico y económico** exhaustivo
5. ✅ **Demo ejecutable** que demuestra concepto
6. ✅ **Documentación production-ready**

**Diferenciadores:**
- Reutilización inteligente del Caso #1
- Arquitectura modular y escalable
- Solución cost-effective ($0.20/llamada)
- Better UX que IVR tradicional
- Disponibilidad 24/7

### Viabilidad para Producción

Esta solución está lista para avanzar a producción con:
- Tiempo estimado: 12-14 semanas desde kick-off
- Inversión inicial: ~$30,000
- Break-even: <1 mes de operación
- ROI anual: >2000% para banco mediano

---

**Fin del Documento - Caso #2**

*Elaborado con visión técnica y estratégica*  
*Carlos Israel Jiménez - Octubre 2025*