#!/usr/bin/env python3
"""
Agente Bancario Conversacional con IA Generativa
Interfaz de consola/terminal

Caso de Evaluación: AI Engineer
"""

import sys
import os
from config.settings import GEMINI_API_KEY, WELCOME_MESSAGE, GOODBYE_MESSAGE
from src.agent import BankingAgent

def print_banner():
    """Muestra el banner de bienvenida"""
    print("\n" + "="*70)
    print("🏦  BANCO NACIONAL DEL ECUADOR - ASISTENTE VIRTUAL  🏦")
    print("="*70)
    print(WELCOME_MESSAGE)
    print("\n💡 Comandos especiales:")
    print("   • 'salir' o 'exit' - Terminar conversación")
    print("   • 'reset' - Cerrar sesión y reiniciar")
    print("   • 'historial' - Ver últimas interacciones")
    print("   • 'sesion' - Ver estado de la sesión")
    print("="*70 + "\n")

def print_separator():
    """Imprime un separador visual"""
    print("-" * 70)

def print_help():
    """Muestra ayuda al usuario"""
    print("\n📚 AYUDA - ¿Qué puedes hacer?")
    print("\n1️⃣  Preguntas Generales (sin autenticación):")
    print("   • ¿Cuáles son los horarios de atención?")
    print("   • ¿Cómo abrir una cuenta de ahorros?")
    print("   • ¿Qué tipos de seguros ofrecen?")
    print("   • ¿Cuánto cobran por transferencias?")
    
    print("\n2️⃣  Consultas Personales (requiere autenticación):")
    print("   • ¿Cuál es mi saldo?")
    print("   • Muéstrame mis tarjetas")
    print("   • Mis últimos movimientos")
    print("   • Información de mis pólizas")
    
    print("\n3️⃣  Autenticación:")
    print("   Usuario: Quiero consultar mi saldo")
    print("   Bot: [Solicita autenticación]")
    print("   Usuario: Mi cédula es 1234567890 y el código es 123456")
    
    print("\n💡 Credenciales de prueba:")
    print("   Cédula: 1234567890")
    print("   Código OTP: 123456")
    print()

def main():
    """Función principal - Modo interactivo"""
    
    # Verificar API key
    if not GEMINI_API_KEY:
        print("❌ Error: No se encontró GEMINI_API_KEY")
        print("Por favor configura la variable de entorno o modifica config/settings.py")
        sys.exit(1)
    
    # Inicializar agente
    try:
        agent = BankingAgent(GEMINI_API_KEY)
    except Exception as e:
        print(f"❌ Error al inicializar el agente: {e}")
        sys.exit(1)
    
    # Mostrar banner
    print_banner()
    
    # Loop principal de conversación
    while True:
        try:
            # Obtener input del usuario
            user_input = input("\n👤 Tú: ").strip()
            
            if not user_input:
                continue
            
            # Comandos especiales
            if user_input.lower() in ['salir', 'exit', 'quit', 'bye', 'adios']:
                print(f"\n🤖 Asistente: {GOODBYE_MESSAGE}\n")
                break
            
            if user_input.lower() == 'reset':
                agent.reset_session()
                print("\n🤖 Asistente: Sesión cerrada. ¿En qué puedo ayudarte? 🔓\n")
                continue
            
            if user_input.lower() in ['historial', 'history']:
                print("\n📜 Historial de conversación (últimos 10 mensajes):")
                history = agent.get_conversation_history(10)
                for msg in history:
                    role = "👤 Tú" if msg["role"] == "user" else "🤖 Asistente"
                    print(f"{role}: {msg['content'][:80]}...")
                print()
                continue
            
            if user_input.lower() in ['sesion', 'session', 'info']:
                session_info = agent.get_session_info()
                if session_info:
                    print(f"\n🔐 Sesión activa:")
                    print(f"   Usuario: {session_info['user_name']}")
                    print(f"   Tiempo restante: {session_info['minutes_remaining']} minutos")
                    print(f"   Última actividad: {session_info['last_activity']}")
                else:
                    print("\n🔓 No hay sesión activa")
                print()
                continue
            
            if user_input.lower() in ['ayuda', 'help', '?']:
                print_help()
                continue
            
            # Procesar mensaje con el agente
            print("\n🤖 Asistente: ", end="", flush=True)
            response = agent.process_message(user_input)
            print(response)
            
            print_separator()
            
        except KeyboardInterrupt:
            print(f"\n\n🤖 Asistente: {GOODBYE_MESSAGE}\n")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            print("Por favor intenta de nuevo o escribe 'salir' para terminar.\n")

def demo_mode():
    """
    Modo demostración con conversación pregrabada.
    Útil para presentaciones y testing rápido.
    """
    print("\n" + "="*70)
    print("🎬  MODO DEMOSTRACIÓN - AGENTE BANCARIO")
    print("="*70)
    print("\nEsta es una demostración automatizada del agente.\n")
    
    try:
        agent = BankingAgent(GEMINI_API_KEY)
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")
        return
    
    # Conversación de demostración
    demo_conversation = [
        ("¡Hola! ¿Me puedes ayudar?", 2),
        ("¿Cuáles son los horarios de atención?", 2),
        ("¿Cómo puedo abrir una cuenta de ahorros?", 2),
        ("Necesito consultar mi saldo", 2),
        ("Mi cédula es 1234567890 y el código es 123456", 2),
        ("Ahora sí, ¿cuál es mi saldo?", 2),
        ("Muéstrame mis tarjetas", 2),
        ("¿Tengo pólizas de seguro?", 2),
        ("¿Cuánto cobran por transferencias?", 2),
        ("Gracias, eso es todo", 2),
    ]
    
    print("🤖 Asistente: " + WELCOME_MESSAGE)
    print("\n" + "-"*70 + "\n")
    
    import time
    
    for i, (message, pause) in enumerate(demo_conversation, 1):
        print(f"\n[Interacción {i}/{len(demo_conversation)}]")
        print(f"👤 Usuario: {message}")
        print("🤖 Asistente: ", end="", flush=True)
        
        response = agent.process_message(message)
        print(response)
        
        print("\n" + "-"*70)
        time.sleep(pause)
    
    print("\n✅ Demostración completada\n")
    print("="*70)
    print("Para usar el agente interactivamente, ejecuta: python main.py")
    print("="*70 + "\n")

def run_tests():
    """Ejecuta tests básicos del agente"""
    print("\n🧪 Ejecutando tests básicos...\n")
    
    try:
        agent = BankingAgent(GEMINI_API_KEY)
        
        test_cases = [
            ("¿Horarios de atención?", "FAQ"),
            ("Mi cédula es 1234567890 y código 123456", "Autenticación"),
        ]
        
        passed = 0
        failed = 0
        
        for query, expected_type in test_cases:
            print(f"Test: {expected_type}")
            print(f"  Query: {query}")
            try:
                response = agent.process_message(query)
                print(f"  ✅ Respuesta recibida ({len(response)} chars)")
                passed += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1
            print()
        
        print(f"\n📊 Resultados: {passed} exitosos, {failed} fallidos")
        
    except Exception as e:
        print(f"❌ Error en tests: {e}")

if __name__ == "__main__":
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "--demo":
            demo_mode()
        elif mode == "--test":
            run_tests()
        elif mode == "--help":
            print("\nUso: python main.py [OPCIÓN]")
            print("\nOpciones:")
            print("  (sin opción)  Modo interactivo normal")
            print("  --demo        Ejecuta demostración automatizada")
            print("  --test        Ejecuta tests básicos")
            print("  --help        Muestra esta ayuda")
            print()
        else:
            print(f"❌ Opción desconocida: {mode}")
            print("Usa --help para ver las opciones disponibles")
    else:
        # Modo interactivo normal
        main()