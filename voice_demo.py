#!/usr/bin/env python3
"""
Demo del Agente Bancario de Voz - Caso #2
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.voice_agent import VoiceAgent
from config.settings import GEMINI_API_KEY


def print_banner():
    print("\n" + "="*70)
    print("🎙️  DEMO: AGENTE BANCARIO DE VOZ - CASO #2")
    print("="*70)
    print("\nEste demo muestra la arquitectura del agente de voz.")
    print("Usa Google Cloud Text-to-Speech y Speech-to-Text.")
    print("="*70 + "\n")


def demo_text_to_speech():
    """Demo de TTS"""
    print("\n" + "─"*70)
    print("📌 DEMO: Generación de Voz (TTS)")
    print("─"*70)
    
    try:
        agent = VoiceAgent(GEMINI_API_KEY)
        
        messages = [
            "¡Hola! Bienvenido al Banco Nacional del Ecuador.",
            "Tu saldo disponible es cinco mil cuatrocientos veinte dólares.",
            "Por tu seguridad, necesito verificar tu identidad."
        ]
        
        for i, msg in enumerate(messages, 1):
            print(f"\n[Mensaje {i}]")
            print(f"📝 Texto: {msg}")
            
            output = f"demo_tts_{i}.mp3"
            result = agent.synthesize_speech(msg, output)
            
            if result["success"]:
                print(f"✅ Audio: {output}")
            else:
                print(f"❌ Error: {result.get('error')}")
        
        print("\n✅ Demo completado")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Asegúrate de tener GOOGLE_CLOUD_API_KEY en tu .env")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_integration():
    """Demo de integración con BankingAgent"""
    print("\n" + "─"*70)
    print("📌 DEMO: Integración con Agente Bancario")
    print("─"*70)
    
    try:
        agent = VoiceAgent(GEMINI_API_KEY)
        
        queries = [
            "¿Cuál es el horario de atención?",
            "¿Cómo abrir una cuenta de ahorros?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n[Query {i}]")
            print(f"👤 Usuario: {query}")
            
            # Procesar con agente
            response = agent.text_agent.process_message(query)
            print(f"🤖 Agente: {response[:150]}...")
            
            # Generar audio
            output = f"demo_query_{i}.mp3"
            result = agent.synthesize_speech(response, output)
            
            if result["success"]:
                print(f"✅ Audio: {output}")
        
        print("\n✅ Demo completado")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def show_architecture():
    """Muestra arquitectura"""
    print("\n" + "─"*70)
    print("📌 ARQUITECTURA DEL SISTEMA")
    print("─"*70)
    
    print("""
🎙️  FLUJO DE VOZ EN TIEMPO REAL:

1️⃣  Usuario habla por teléfono
    ↓
2️⃣  Twilio recibe audio → WebSocket streaming
    ↓
3️⃣  SPEECH-TO-TEXT (Google Cloud)
    • Audio → Texto en español
    • Latencia: ~500ms
    ↓
4️⃣  BANKING AGENT (Gemini - Reutilizado)
    • Procesa texto
    • Ejecuta tools
    • Genera respuesta
    • Latencia: ~1-2s
    ↓
5️⃣  TEXT-TO-SPEECH (Google Cloud)
    • Texto → Audio natural
    • Voz en español
    • Latencia: ~300ms
    ↓
6️⃣  Audio streaming → Usuario

⏱️  LATENCIA TOTAL: ~2-3 segundos

💰 COSTOS (llamada de 5 min):
    • Twilio: $0.065
    • Google STT: $0.006/15s = $0.12
    • Google TTS: $4/1M chars ≈ $0.02
    • TOTAL: ~$0.20 por llamada

🎯 VENTAJAS:
    ✅ Mismo ecosistema Google (Gemini + Cloud)
    ✅ Voces naturales en español
    ✅ Escalable y costo-efectivo
    """)


def show_stats():
    """Muestra estadísticas"""
    print("\n" + "─"*70)
    print("📊 ESTADÍSTICAS")
    print("─"*70)
    
    try:
        agent = VoiceAgent(GEMINI_API_KEY)
        stats = agent.get_statistics()
        
        print(f"""
🎙️  Configuración:
    • Provider: {stats['provider']}
    • Voz: {stats['voice']}
    • Velocidad: {stats['speed']}x
        """)
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Función principal"""
    print_banner()
    
    # Verificar configuración
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no configurada")
        return
    
    if not os.getenv('GOOGLE_CLOUD_API_KEY'):
        print("⚠️  GOOGLE_CLOUD_API_KEY no configurada")
        print("   Agrégala a tu .env para usar funciones de voz\n")
    
    while True:
        print("\n" + "="*70)
        print("DEMOS DISPONIBLES:")
        print("="*70)
        print("1. Generación de Voz (TTS)")
        print("2. Integración con Agente Bancario")
        print("3. Arquitectura del Sistema")
        print("4. Estadísticas")
        print("5. Ejecutar todos")
        print("0. Salir")
        print("="*70)
        
        choice = input("\nSelecciona: ").strip()
        
        if choice == "1":
            demo_text_to_speech()
        elif choice == "2":
            demo_integration()
        elif choice == "3":
            show_architecture()
        elif choice == "4":
            show_stats()
        elif choice == "5":
            demo_text_to_speech()
            demo_integration()
            show_architecture()
            show_stats()
        elif choice == "0":
            print("\n👋 ¡Hasta luego!\n")
            break
        else:
            print("\n❌ Opción inválida")
        
        input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrumpido\n")