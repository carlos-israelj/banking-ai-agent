"""
Agente Bancario de Voz - Caso #2
Usa Google Cloud TTS/STT con Service Account (JSON)
"""

import os
import logging
from typing import Dict
from pathlib import Path

try:
    from google.cloud import texttospeech
    from google.cloud import speech
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("⚠️  Google Cloud libraries no disponibles")

from src.agent import BankingAgent
from config.settings import GEMINI_API_KEY

logger = logging.getLogger(__name__)


class VoiceAgent:
    """
    Agente bancario con capacidades de voz usando Google Cloud.
    Autenticación vía Service Account (archivo JSON).
    """
    
    def __init__(self, gemini_api_key: str = GEMINI_API_KEY):
        """Inicializa el agente de voz"""
        
        if not GOOGLE_CLOUD_AVAILABLE:
            raise ImportError(
                "Instala: pip install google-cloud-texttospeech google-cloud-speech"
            )
        
        # Verificar credenciales
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS no configurada.\n"
                "Agrégala a tu .env:\n"
                "GOOGLE_APPLICATION_CREDENTIALS=credentials/google-cloud-key.json"
            )
        
        if not Path(credentials_path).exists():
            raise ValueError(
                f"Archivo de credenciales no encontrado: {credentials_path}"
            )
        
        # Agente base
        self.text_agent = BankingAgent(gemini_api_key)
        
        # Clientes de Google Cloud (usan GOOGLE_APPLICATION_CREDENTIALS automáticamente)
        try:
            self.tts_client = texttospeech.TextToSpeechClient()
            self.stt_client = speech.SpeechClient()
            logger.info("Clientes de Google Cloud inicializados con Service Account")
        except Exception as e:
            logger.error(f"Error al inicializar clientes: {e}")
            raise
        
        # Configuración de voz
        self.voice_config = texttospeech.VoiceSelectionParams(
            language_code="es-ES",
            name="es-ES-Standard-A",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        self.last_response_text = ""
        logger.info("VoiceAgent (Google Cloud Service Account) inicializado")
    
    def transcribe_audio(self, audio_file_path: str) -> Dict:
        """Transcribe audio a texto usando Google Cloud Speech-to-Text"""
        try:
            logger.info(f"Transcribiendo: {audio_file_path}")
            
            if not Path(audio_file_path).exists():
                return {
                    "success": False,
                    "error": "FILE_NOT_FOUND"
                }
            
            # Leer audio
            with open(audio_file_path, 'rb') as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=16000,
                language_code="es-ES",
                enable_automatic_punctuation=True
            )
            
            # Transcribir
            response = self.stt_client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    "success": False,
                    "error": "NO_SPEECH_DETECTED"
                }
            
            transcript = response.results[0].alternatives[0].transcript
            confidence = response.results[0].alternatives[0].confidence
            
            logger.info(f"Transcripción: {transcript}")
            
            return {
                "success": True,
                "text": transcript,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error STT: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def synthesize_speech(
        self, 
        text: str, 
        output_file: str = "response.mp3",
        speed: float = None
    ) -> Dict:
        """Convierte texto a voz usando Google Cloud Text-to-Speech"""
        try:
            logger.info(f"Sintetizando: {text[:50]}...")
            
            # Preparar texto
            text_clean = self._prepare_text_for_speech(text)
            
            # Input
            synthesis_input = texttospeech.SynthesisInput(text=text_clean)
            
            # Config de audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed if speed else 1.0,
                pitch=0.0
            )
            
            # Sintetizar
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice_config,
                audio_config=audio_config
            )
            
            # Guardar
            with open(output_file, 'wb') as out:
                out.write(response.audio_content)
            
            logger.info(f"Audio generado: {output_file}")
            
            return {
                "success": True,
                "audio_file": output_file,
                "text": text_clean,
                "duration_estimate": len(text_clean) / 15
            }
            
        except Exception as e:
            logger.error(f"Error TTS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_text_for_speech(self, text: str) -> str:
        """Limpia texto para voz"""
        replacements = {
            "USD": "dólares",
            "$": "dólares ",
            "✅": "", "❌": "",
            "🏦": "", "💳": "",
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return " ".join(result.split())
    
    def process_voice_interaction(
        self, 
        input_audio: str,
        output_audio: str = "response.mp3"
    ) -> Dict:
        """Procesa interacción completa de voz"""
        logger.info("="*70)
        logger.info("🎙️  Interacción de voz")
        logger.info("="*70)
        
        # STT
        logger.info("1️⃣  Speech-to-Text...")
        stt_result = self.transcribe_audio(input_audio)
        
        if not stt_result["success"]:
            return {"success": False, "error": "STT_FAILED"}
        
        user_text = stt_result["text"]
        logger.info(f"📝 Usuario: {user_text}")
        
        # Agente
        logger.info("2️⃣  Procesando...")
        response = self.text_agent.process_message(user_text)
        logger.info(f"💬 Respuesta: {response[:100]}...")
        
        self.last_response_text = response
        
        # TTS
        logger.info("3️⃣  Text-to-Speech...")
        tts_result = self.synthesize_speech(response, output_audio)
        
        if not tts_result["success"]:
            return {"success": False, "error": "TTS_FAILED"}
        
        logger.info("✅ Completado")
        logger.info("="*70)
        
        return {
            "success": True,
            "user_text": user_text,
            "agent_text": response,
            "audio_file": output_audio
        }
    
    def adjust_speech_speed(self, speed: float):
        """Ajusta velocidad (0.25-4.0)"""
        if 0.25 <= speed <= 4.0:
            self.audio_config.speaking_rate = speed
    
    def get_statistics(self) -> Dict:
        """Estadísticas"""
        return {
            "provider": "Google Cloud (Service Account)",
            "voice": self.voice_config.name,
            "speed": self.audio_config.speaking_rate
        }