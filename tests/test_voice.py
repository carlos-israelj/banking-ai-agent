"""
Tests para el Voice Agent - Caso #2
"""

import pytest
import os
from pathlib import Path
from src.voice_agent import VoiceAgent


class TestVoiceAgent:
    """Suite de tests para VoiceAgent"""
    
    @pytest.fixture
    def agent(self):
        """Fixture: Instancia de VoiceAgent para tests"""
        gemini_key = os.getenv('GEMINI_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not gemini_key or not openai_key:
            pytest.skip("API keys no configuradas")
        
        return VoiceAgent(gemini_key)
    
    def test_agent_initialization(self, agent):
        """Test: Agente se inicializa correctamente"""
        assert agent is not None
        assert agent.text_agent is not None
        assert agent.openai_client is not None
        assert agent.voice_config["voice"] == "nova"
    
    def test_text_preparation_for_speech(self, agent):
        """Test: Preparación de texto para voz"""
        # Texto con símbolos
        input_text = "Tu saldo es $5,420.50 USD ✅"
        expected = "Tu saldo es dólares 5,420.50 dólares "
        
        result = agent._prepare_text_for_speech(input_text)
        
        # Verificar que se eliminaron símbolos
        assert "✅" not in result
        assert "USD" not in result
        assert "dólares" in result
    
    def test_speech_synthesis(self, agent):
        """Test: Síntesis de voz funciona"""
        text = "Hola, este es un test"
        output_file = "test_output.mp3"
        
        result = agent.synthesize_speech(text, output_file)
        
        assert result["success"] == True
        assert Path(output_file).exists()
        assert result["audio_file"] == output_file
        
        # Limpiar
        if Path(output_file).exists():
            Path(output_file).unlink()
    
    def test_speech_speed_adjustment(self, agent):
        """Test: Ajuste de velocidad de habla"""
        # Velocidad normal
        agent.adjust_speech_speed(1.0)
        assert agent.voice_config["speed"] == 1.0
        
        # Más lento
        agent.adjust_speech_speed(0.85)
        assert agent.voice_config["speed"] == 0.85
        
        # Más rápido
        agent.adjust_speech_speed(1.15)
        assert agent.voice_config["speed"] == 1.15
        
        # Fuera de rango (no debería cambiar)
        agent.adjust_speech_speed(5.0)
        assert agent.voice_config["speed"] == 1.15  # Se mantiene
    
    def test_voice_change(self, agent):
        """Test: Cambio de voz"""
        # Voz por defecto
        assert agent.voice_config["voice"] == "nova"
        
        # Cambiar a otra voz
        agent.change_voice("alloy")
        assert agent.voice_config["voice"] == "alloy"
        
        # Voz inválida (no debería cambiar)
        agent.change_voice("invalid_voice")
        assert agent.voice_config["voice"] == "alloy"  # Se mantiene
    
    def test_integration_with_banking_agent(self, agent):
        """Test: Integración con BankingAgent"""
        # Query simple
        query = "¿Cuál es el horario de atención?"
        response = agent.text_agent.process_message(query)
        
        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)
    
    def test_repeat_last_response(self, agent):
        """Test: Repetir última respuesta"""
        # Sin respuesta previa
        result = agent.repeat_last_response()
        assert result["success"] == False
        assert result["error"] == "NO_PREVIOUS_RESPONSE"
        
        # Con respuesta previa
        agent.last_response_text = "Test response"
        result = agent.repeat_last_response(output_file="test_repeat.mp3")
        assert result["success"] == True
        
        # Limpiar
        if Path("test_repeat.mp3").exists():
            Path("test_repeat.mp3").unlink()
    
    def test_statistics(self, agent):
        """Test: Obtención de estadísticas"""
        stats = agent.get_statistics()
        
        assert stats["voice_enabled"] == True
        assert "stt_model" in stats
        assert "tts_model" in stats
        assert "voice" in stats
        assert "speech_speed" in stats


# Tests de integración (requieren archivos de audio)
class TestVoiceIntegration:
    """Tests de integración que requieren audio real"""
    
    @pytest.mark.skipif(
        not Path("test_audio.mp3").exists(),
        reason="Archivo de audio de test no disponible"
    )
    def test_full_voice_interaction(self):
        """Test: Interacción completa de voz"""
        agent = VoiceAgent(os.getenv('GEMINI_API_KEY'))
        
        result = agent.process_voice_interaction(
            "test_audio.mp3",
            "test_response.mp3"
        )
        
        assert result["success"] == True
        assert "user_text" in result
        assert "agent_text" in result
        assert Path(result["agent_audio"]).exists()
        
        # Limpiar
        if Path("test_response.mp3").exists():
            Path("test_response.mp3").unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])