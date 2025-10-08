"""
Agente conversacional bancario principal.
"""
import json
import google.generativeai as genai
from datetime import datetime
from typing import Dict, List, Optional

from config.settings import GEMINI_API_KEY, MODEL_NAME, MODEL_TEMPERATURE
from config.prompts import get_system_prompt
from src.tools import BankingTools
from src.knowledge import KnowledgeBase, search_knowledge_base
from src.security import SecurityManager

class BankingAgent:
    """
    Agente conversacional bancario basado en Gemini.
    """
    
    def __init__(self, api_key: str = GEMINI_API_KEY):
        # Configurar Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config={
                "temperature": MODEL_TEMPERATURE,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        # Inicializar componentes
        self.tools = BankingTools()
        self.knowledge = KnowledgeBase()
        self.security = SecurityManager()
        
        # Estado de la conversación
        self.conversation_history = []
        self.session_token = None
        self.session_data = None
        self.current_user_id = None
        
        print("✅ Agente bancario inicializado correctamente")
    
    def process_message(self, user_message: str) -> str:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        """
        
        # 1. Validar input
        validation = self.security.validate_input(user_message)
        if not validation["valid"]:
            return f"⚠️  {validation['reason']}. Por favor, reformula tu mensaje."
        
        # 2. Rate limiting
        if self.current_user_id:
            rate_check = self.security.check_rate_limit(self.current_user_id)
            if not rate_check["allowed"]:
                reset_time = rate_check["reset_time"].strftime("%H:%M")
                return f"⚠️  Has alcanzado el límite de solicitudes. Por favor intenta de nuevo a las {reset_time}."
        
        # 3. Buscar contexto relevante en la base de conocimiento
        knowledge_context = ""
        if self._is_general_query(user_message):
            kb_results = search_knowledge_base(user_message)
            if kb_results.get("success"):
                knowledge_context = f"\n[INFORMACIÓN RELEVANTE]:\n{kb_results['results']}\n"
        
        # 4. Construir prompt completo
        system_prompt = self._build_system_prompt(knowledge_context)
        system_prompt += "\n\nIMPORTANTE: Responde en texto natural conversacional. NO uses JSON excepto para herramientas bancarias específicas."
        
        # 5. Agregar mensaje al historial
        self._add_to_history("user", user_message)
        
        try:
            # 6. Generar respuesta con Gemini
            full_prompt = self._build_full_prompt(system_prompt, user_message)
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            # 7. Detectar si es una llamada a herramienta
            if self._is_tool_call(response_text):
                response_text = self._handle_tool_call(response_text)
            else:
                # Si viene JSON cuando no debería, responder apropiadamente
                if response_text.startswith('{'):
                    msg_lower = user_message.lower()
                    if "hola" in msg_lower or "buenos" in msg_lower or "hi" in msg_lower:
                        response_text = "¡Hola! 👋 ¿En qué puedo ayudarte hoy?"
                    elif "horario" in msg_lower:
                        response_text = "Nuestros horarios son: Lunes a Viernes de 8 AM a 5 PM, Sábados de 9 AM a 1 PM. 🏦"
                    else:
                        response_text = "¿En qué puedo ayudarte? Puedo responder sobre productos bancarios o tus cuentas. 😊"
            
            # 8. Sanitizar output
            is_authenticated = self.session_data is not None
            response_text = self.security.sanitize_output(response_text, is_authenticated)
            
            # 9. Agregar respuesta al historial
            self._add_to_history("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            self._log_error(str(e))
            return "Disculpa, tuve un problema técnico. ¿Puedes reformular tu pregunta? 😊"
    
    def _build_system_prompt(self, knowledge_context: str = "") -> str:
        """Construye el system prompt con contexto actual"""
        authenticated = self.session_data is not None
        
        user_data = None
        if authenticated and self.session_data:
            user_data = {
                "name": self.session_data.get("user_name", "Usuario"),
                "user_id": self.session_data.get("user_id"),
                "session_expiry": self.session_data.get("expires_at")
            }
        
        base_prompt = get_system_prompt(authenticated, user_data)
        
        if knowledge_context:
            base_prompt += knowledge_context
        
        return base_prompt
    
    def _build_full_prompt(self, system_prompt: str, user_message: str) -> str:
        """Construye el prompt completo con historial"""
        prompt_parts = [system_prompt]
        
        # Agregar últimos N mensajes del historial para contexto
        recent_history = self.conversation_history[-6:]  # Últimos 3 intercambios
        if recent_history:
            prompt_parts.append("\n[HISTORIAL RECIENTE DE LA CONVERSACIÓN]:")
            for msg in recent_history:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                prompt_parts.append(f"{role}: {msg['content']}")
        
        # Mensaje actual
        prompt_parts.append(f"\nUsuario: {user_message}")
        prompt_parts.append("Asistente:")
        
        return "\n".join(prompt_parts)
    
    def _is_general_query(self, message: str) -> bool:
        """Detecta si es una consulta general que requiere buscar en FAQs"""
        general_keywords = [
            "horario", "requisito", "cómo", "como", "qué es", "que es",
            "diferencia", "tasa", "interés", "comisión", "cobran",
            "ofrecen", "tipos de", "solicitar", "abrir"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in general_keywords)
    
    def _is_tool_call(self, response: str) -> bool:
        """Detecta si la respuesta del LLM es una llamada a herramienta"""
        try:
            response = response.strip()
            
            if '{' not in response or '}' not in response:
                return False
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                return False
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            return (
                data.get("action") == "call_tool" and 
                "tool_name" in data and
                data.get("tool_name") in [
                    "authenticate_user",
                    "get_account_balance", 
                    "get_account_movements",
                    "get_card_info",
                    "get_policy_info",
                    "search_knowledge_base"
                ]
            )
        except:
            return False
    
    def _handle_tool_call(self, response: str) -> str:
        """Procesa llamadas a herramientas"""
        try:
            # Extraer JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            tool_request = json.loads(json_str)
            
            tool_name = tool_request["tool_name"]
            parameters = tool_request.get("parameters", {})
            user_message = tool_request.get("user_message", "Un momento por favor...")
            
            # Validar autenticación para tools protegidas
            protected_tools = [
                "get_account_balance",
                "get_account_movements",
                "get_card_info",
                "get_policy_info"
            ]
            
            if tool_name in protected_tools and not self.session_data:
                return "Por tu seguridad, necesito verificar tu identidad primero. ¿Tienes a mano tu cédula? 🔐"
            
            # Ejecutar herramienta correspondiente
            if tool_name == "authenticate_user":
                return self._execute_authenticate(parameters)
            
            elif tool_name == "get_account_balance":
                return self._execute_get_balance(parameters)
            
            elif tool_name == "get_account_movements":
                return self._execute_get_movements(parameters)
            
            elif tool_name == "get_card_info":
                return self._execute_get_cards(parameters)
            
            elif tool_name == "get_policy_info":
                return self._execute_get_policies(parameters)
            
            elif tool_name == "search_knowledge_base":
                return self._execute_search_kb(parameters)
            
            else:
                return "Disculpa, esa operación no está disponible en este momento."
                
        except Exception as e:
            self._log_error(f"Tool error: {str(e)}")
            return "Tuve un problema al procesar tu solicitud. ¿Puedo ayudarte con algo más? 😊"
    
    def _execute_authenticate(self, parameters: Dict) -> str:
        """Ejecuta autenticación del usuario"""
        document_id = parameters.get("document_id")
        otp_code = parameters.get("otp_code")
        
        if not document_id:
            return "Necesito tu número de cédula para autenticarte. ¿Puedes proporcionarla?"
        
        result = self.tools.authenticate_user(document_id, otp_code)
        
        if result["success"]:
            # Crear sesión
            self.session_token = self.security.create_session(
                result["user_id"],
                result
            )
            is_valid, session = self.security.validate_session(self.session_token)
            self.session_data = session
            self.current_user_id = result["user_id"]
            
            return f"✅ ¡Perfecto! Autenticación exitosa. Hola {result['user_name']} 👋\n\n¿En qué puedo ayudarte hoy?"
        
        else:
            error = result.get("error")
            if error == "USER_NOT_FOUND":
                return "No encontré un usuario registrado con esa cédula. ¿Puedes verificar el número?"
            elif error == "INVALID_OTP":
                return "El código de verificación no es correcto. ¿Quieres que te envíe uno nuevo?"
            elif error == "SERVICE_UNAVAILABLE":
                return "Estoy teniendo problemas técnicos. ¿Puedes intentar en unos minutos? 🙏"
            else:
                return "No pude completar la autenticación. ¿Quieres intentar de nuevo?"
    
    def _execute_get_balance(self, parameters: Dict) -> str:
        """Ejecuta consulta de saldo"""
        if not self.session_data:
            return "Por seguridad, necesito que te autentiques primero."
        
        user_id = self.session_data["user_id"]
        account_type = parameters.get("account_type")
        
        result = self.tools.get_account_balance(user_id, account_type)
        
        if result["success"]:
            accounts = result["data"]
            if len(accounts) == 1:
                acc = accounts[0]
                return f"""💳 **Cuenta {acc['account_type'].title()}**
Número: {acc['account_number']}
Saldo disponible: ${acc['balance']:,.2f} {acc['currency']}
Estado: {acc['status']}
Actualizado: {acc['last_updated']}

¿Necesitas algo más?"""
            else:
                response = "💳 **Tus Cuentas:**\n\n"
                for acc in accounts:
                    response += f"• {acc['account_type'].title()}: ${acc['balance']:,.2f} {acc['currency']}\n"
                response += "\n¿Quieres detalles de alguna cuenta en específico?"
                return response
        else:
            return "No pude consultar tu saldo en este momento. ¿Quieres que intente de nuevo?"
    
    def _execute_get_movements(self, parameters: Dict) -> str:
        """Ejecuta consulta de movimientos"""
        if not self.session_data:
            return "Por seguridad, necesito que te autentiques primero."
        
        user_id = self.session_data["user_id"]
        account_type = parameters.get("account_type", "ahorros")
        limit = parameters.get("limit", 5)
        
        result = self.tools.get_account_movements(user_id, account_type, limit)
        
        if result["success"]:
            movements = result["data"]["movements"]
            if not movements:
                return "No encontré movimientos recientes en esa cuenta."
            
            response = f"📊 **Últimos {len(movements)} movimientos - Cuenta {account_type.title()}:**\n\n"
            for mov in movements:
                emoji = "💰" if mov['amount'] > 0 else "💸"
                response += f"{emoji} {mov['date']}: ${abs(mov['amount']):,.2f}\n   {mov['description']}\n\n"
            
            response += "¿Necesitas más información?"
            return response
        else:
            return "No pude consultar los movimientos. ¿Intentamos de nuevo?"
    
    def _execute_get_cards(self, parameters: Dict) -> str:
        """Ejecuta consulta de tarjetas"""
        if not self.session_data:
            return "Por seguridad, necesito que te autentiques primero."
        
        user_id = self.session_data["user_id"]
        card_type = parameters.get("card_type")
        
        result = self.tools.get_card_info(user_id, card_type)
        
        if result["success"]:
            cards = result["data"]
            if not cards:
                return "No encontré tarjetas activas en tu cuenta."
            
            response = "💳 **Tus Tarjetas:**\n\n"
            for card in cards:
                response += f"• {card['card_type'].title()} {card['card_brand']}\n"
                response += f"  Número: **** **** **** {card['last_4_digits']}\n"
                
                if card['card_type'] == 'credit':
                    response += f"  Límite: ${card['credit_limit']:,.2f}\n"
                    response += f"  Disponible: ${card['available_credit']:,.2f}\n"
                
                response += f"  Estado: {card['status']}\n\n"
            
            response += "¿Necesitas algo más sobre tus tarjetas?"
            return response
        else:
            return "No pude consultar la información de tus tarjetas. ¿Intentamos nuevamente?"
    
    def _execute_get_policies(self, parameters: Dict) -> str:
        """Ejecuta consulta de pólizas"""
        if not self.session_data:
            return "Por seguridad, necesito que te autentiques primero."
        
        user_id = self.session_data["user_id"]
        policy_type = parameters.get("policy_type")
        
        result = self.tools.get_policy_info(user_id, policy_type)
        
        if result["success"]:
            policies = result["data"]
            if not policies:
                return "No encontré pólizas activas en tu cuenta."
            
            response = "📄 **Tus Pólizas de Seguro:**\n\n"
            for policy in policies:
                response += f"• {policy['policy_type']}\n"
                response += f"  Póliza: {policy['policy_number']}\n"
                response += f"  Cobertura: ${policy['coverage']:,.2f}\n"
                response += f"  Prima mensual: ${policy['premium']:,.2f}\n"
                response += f"  Vence: {policy['expiry_date']}\n"
                
                if 'vehicle' in policy:
                    response += f"  Vehículo: {policy['vehicle']}\n"
                
                response += "\n"
            
            response += "¿Necesitas más información sobre alguna póliza?"
            return response
        else:
            return "No pude consultar tus pólizas. ¿Intentamos de nuevo?"
    
    def _execute_search_kb(self, parameters: Dict) -> str:
        """Ejecuta búsqueda en base de conocimiento"""
        query = parameters.get("query", "")
        if not query:
            return "No entendí sobre qué quieres información. ¿Puedes ser más específico?"
        
        result = search_knowledge_base(query)
        
        if result["success"]:
            return result["results"] + "\n\n¿Necesitas saber algo más?"
        else:
            return "No encontré información sobre eso. ¿Quieres que te contacte con un asesor? 📞"
    
    def _add_to_history(self, role: str, content: str):
        """Agrega un mensaje al historial de conversación"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener solo los últimos N mensajes
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def _log_error(self, error: str):
        """Registra errores para monitoreo"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "user_id": self.current_user_id or "anonymous",
            "session_active": self.session_data is not None
        }
        print(f"[ERROR] {json.dumps(log_entry)}")
    
    def reset_session(self):
        """Reinicia la sesión del usuario (logout)"""
        if self.session_token:
            self.security.destroy_session(self.session_token)
        
        self.session_token = None
        self.session_data = None
        self.current_user_id = None
        print("✅ Sesión cerrada correctamente")
    
    def get_session_info(self) -> Optional[Dict]:
        """Obtiene información de la sesión actual"""
        if not self.session_token:
            return None
        return self.security.get_session_info(self.session_token)
    
    def get_conversation_history(self, last_n: int = 10) -> List[Dict]:
        """Obtiene el historial de conversación"""
        return self.conversation_history[-last_n:]