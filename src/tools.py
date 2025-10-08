"""
Herramientas (Tools) que el agente puede utilizar.
Estas son simulaciones de APIs reales del banco.
"""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class BankingTools:
    """
    Conjunto de herramientas bancarias que el agente puede invocar.
    En producción, estas se conectarían a APIs reales del core bancario.
    """
    
    def __init__(self):
        # Base de datos simulada de usuarios
        self.users_db = {
            "1234567890": {
                "user_id": "USR001",
                "name": "Juan Pérez",
                "email": "juan.perez@email.com",
                "phone": "0998765432",
                "otp_secret": "123456",  # En producción: generado dinámicamente
                "accounts": [
                    {
                        "account_id": "ACC-001-AHO",
                        "account_type": "ahorros",
                        "account_number": "0001234567",
                        "balance": 5420.50,
                        "currency": "USD",
                        "status": "active",
                        "opening_date": "2020-03-15"
                    },
                    {
                        "account_id": "ACC-001-CTE",
                        "account_type": "corriente",
                        "account_number": "0009876543",
                        "balance": 12300.00,
                        "currency": "USD",
                        "status": "active",
                        "opening_date": "2021-01-10"
                    }
                ],
                "cards": [
                    {
                        "card_id": "CARD-001-CR",
                        "card_type": "credit",
                        "card_brand": "Visa",
                        "card_number": "4532********4532",
                        "last_4_digits": "4532",
                        "credit_limit": 5000.00,
                        "available_credit": 3200.00,
                        "expiry_date": "12/2026",
                        "status": "active"
                    },
                    {
                        "card_id": "CARD-001-DB",
                        "card_type": "debit",
                        "card_brand": "Mastercard",
                        "card_number": "5234********8765",
                        "last_4_digits": "8765",
                        "linked_account": "ACC-001-AHO",
                        "status": "active"
                    }
                ],
                "policies": [
                    {
                        "policy_id": "POL-001-VIDA",
                        "policy_type": "Seguro de Vida",
                        "policy_number": "POL-2024-001",
                        "coverage": 100000.00,
                        "premium": 45.00,
                        "status": "active",
                        "start_date": "2024-01-01",
                        "expiry_date": "2025-12-31"
                    },
                    {
                        "policy_id": "POL-001-AUTO",
                        "policy_type": "Seguro de Auto",
                        "policy_number": "POL-2024-002",
                        "coverage": 25000.00,
                        "premium": 80.00,
                        "status": "active",
                        "start_date": "2024-06-01",
                        "expiry_date": "2025-06-15",
                        "vehicle": "Toyota Corolla 2020"
                    }
                ],
                "movements": [
                    {"date": "2025-10-07", "type": "deposit", "amount": 500.00, "description": "Depósito en ventanilla"},
                    {"date": "2025-10-06", "type": "withdrawal", "amount": -200.00, "description": "Retiro cajero ATM"},
                    {"date": "2025-10-05", "type": "transfer", "amount": -150.00, "description": "Transferencia a Jorge M."},
                    {"date": "2025-10-04", "type": "payment", "amount": -45.50, "description": "Pago tarjeta crédito"},
                    {"date": "2025-10-03", "type": "deposit", "amount": 1200.00, "description": "Salario"},
                ]
            }
        }
    
    def authenticate_user(self, document_id: str, otp_code: str = None) -> Dict:
        """
        Tool: authenticate_user
        
        Propósito:
        Autenticar la identidad del usuario mediante cédula y código OTP.
        
        Entradas esperadas:
        - document_id (str): Número de cédula del usuario
        - otp_code (str, opcional): Código OTP de 6 dígitos
        
        Salida esperada:
        {
            "success": bool,
            "user_id": str,
            "user_name": str,
            "message": str,
            "session_token": str (si success=True)
        }
        
        Posibles errores:
        - USER_NOT_FOUND: Cédula no registrada
        - INVALID_OTP: Código OTP incorrecto
        - SERVICE_UNAVAILABLE: Servicio temporalmente no disponible
        - ACCOUNT_LOCKED: Cuenta bloqueada por múltiples intentos
        
        Manejo del agente:
        - Si USER_NOT_FOUND: Informar amablemente y sugerir registro
        - Si INVALID_OTP: Permitir reintento, ofrecer reenvío de código
        - Si SERVICE_UNAVAILABLE: Disculparse, sugerir intentar más tarde
        - Si ACCOUNT_LOCKED: Informar al usuario contactar soporte
        """
        try:
            # Simular latencia de red
            time.sleep(random.uniform(0.3, 0.8))
            
            # Simular 5% de fallos de servicio
            if random.random() < 0.05:
                return {
                    "success": False,
                    "error": "SERVICE_UNAVAILABLE",
                    "message": "Servicio de autenticación temporalmente no disponible"
                }
            
            # Validar que el usuario existe
            if document_id not in self.users_db:
                return {
                    "success": False,
                    "error": "USER_NOT_FOUND",
                    "message": "No encontramos un usuario registrado con esa cédula"
                }
            
            user = self.users_db[document_id]
            
            # Validar OTP si se proporciona
            if otp_code:
                if otp_code != user["otp_secret"]:
                    return {
                        "success": False,
                        "error": "INVALID_OTP",
                        "message": "El código de verificación es incorrecto"
                    }
            
            # Autenticación exitosa
            session_token = f"SESSION_{document_id}_{int(time.time())}"
            
            return {
                "success": True,
                "user_id": user["user_id"],
                "user_name": user["name"],
                "document_id": document_id,
                "session_token": session_token,
                "message": "Autenticación exitosa"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "UNKNOWN_ERROR",
                "message": f"Error inesperado: {str(e)}"
            }
    
    def get_account_balance(self, user_id: str, account_type: str = None) -> Dict:
        """
        Tool: get_account_balance
        
        Propósito:
        Consultar el saldo disponible de una o todas las cuentas del usuario.
        
        Entradas esperadas:
        - user_id (str): ID del usuario autenticado
        - account_type (str, opcional): Tipo de cuenta ("ahorros" o "corriente")
        
        Salida esperada:
        {
            "success": bool,
            "data": [
                {
                    "account_type": str,
                    "account_number": str (parcialmente enmascarado),
                    "balance": float,
                    "currency": str,
                    "status": str
                }
            ]
        }
        
        Posibles errores:
        - AUTH_REQUIRED: Usuario no autenticado
        - ACCOUNT_NOT_FOUND: No se encontró cuenta del tipo especificado
        - SERVICE_UNAVAILABLE: Error al consultar el servicio
        """
        try:
            # Buscar usuario por user_id
            user_data = None
            for doc_id, data in self.users_db.items():
                if data["user_id"] == user_id:
                    user_data = data
                    break
            
            if not user_data:
                return {
                    "success": False,
                    "error": "AUTH_REQUIRED",
                    "message": "Usuario no autenticado o sesión expirada"
                }
            
            accounts = user_data["accounts"]
            
            # Filtrar por tipo si se especifica
            if account_type:
                accounts = [acc for acc in accounts if acc["account_type"] == account_type]
                if not accounts:
                    return {
                        "success": False,
                        "error": "ACCOUNT_NOT_FOUND",
                        "message": f"No se encontró cuenta de tipo {account_type}"
                    }
            
            # Formatear respuesta
            result = []
            for acc in accounts:
                result.append({
                    "account_type": acc["account_type"],
                    "account_number": f"****{acc['account_number'][-4:]}",
                    "balance": acc["balance"],
                    "currency": acc["currency"],
                    "status": acc["status"],
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "SERVICE_UNAVAILABLE",
                "message": "Error al consultar saldo"
            }
    
    def get_account_movements(self, user_id: str, account_type: str = "ahorros", 
                             limit: int = 5) -> Dict:
        """
        Tool: get_account_movements
        
        Propósito:
        Obtener los últimos movimientos de una cuenta.
        
        Entradas esperadas:
        - user_id (str): ID del usuario autenticado
        - account_type (str): Tipo de cuenta
        - limit (int): Número de movimientos a retornar (default: 5)
        
        Salida esperada:
        {
            "success": bool,
            "data": {
                "account_type": str,
                "movements": [
                    {
                        "date": str,
                        "type": str,
                        "amount": float,
                        "description": str
                    }
                ]
            }
        }
        """
        try:
            user_data = None
            for doc_id, data in self.users_db.items():
                if data["user_id"] == user_id:
                    user_data = data
                    break
            
            if not user_data:
                return {
                    "success": False,
                    "error": "AUTH_REQUIRED",
                    "message": "Usuario no autenticado"
                }
            
            movements = user_data.get("movements", [])[:limit]
            
            return {
                "success": True,
                "data": {
                    "account_type": account_type,
                    "movements": movements,
                    "count": len(movements)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "SERVICE_UNAVAILABLE",
                "message": "Error al consultar movimientos"
            }
    
    def get_card_info(self, user_id: str, card_type: str = None) -> Dict:
        """
        Tool: get_card_info
        
        Propósito:
        Obtener información de las tarjetas del usuario.
        
        Entradas esperadas:
        - user_id (str): ID del usuario autenticado
        - card_type (str, opcional): "credit" o "debit"
        
        Salida esperada:
        {
            "success": bool,
            "data": [
                {
                    "card_type": str,
                    "card_brand": str,
                    "last_4_digits": str,
                    "credit_limit": float (solo crédito),
                    "available_credit": float (solo crédito),
                    "status": str
                }
            ]
        }
        """
        try:
            user_data = None
            for doc_id, data in self.users_db.items():
                if data["user_id"] == user_id:
                    user_data = data
                    break
            
            if not user_data:
                return {
                    "success": False,
                    "error": "AUTH_REQUIRED",
                    "message": "Usuario no autenticado"
                }
            
            cards = user_data["cards"]
            
            # Filtrar por tipo si se especifica
            if card_type:
                cards = [card for card in cards if card["card_type"] == card_type]
            
            if not cards:
                return {
                    "success": False,
                    "error": "CARD_NOT_FOUND",
                    "message": "No se encontraron tarjetas"
                }
            
            # Formatear respuesta (nunca exponer número completo)
            result = []
            for card in cards:
                card_info = {
                    "card_type": card["card_type"],
                    "card_brand": card["card_brand"],
                    "last_4_digits": card["last_4_digits"],
                    "status": card["status"]
                }
                
                if card["card_type"] == "credit":
                    card_info["credit_limit"] = card.get("credit_limit")
                    card_info["available_credit"] = card.get("available_credit")
                    card_info["expiry_date"] = card.get("expiry_date")
                
                result.append(card_info)
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "SERVICE_UNAVAILABLE",
                "message": "Error al consultar tarjetas"
            }
    
    def get_policy_info(self, user_id: str, policy_type: str = None) -> Dict:
        """
        Tool: get_policy_info
        
        Propósito:
        Consultar pólizas de seguro activas del usuario.
        
        Entradas esperadas:
        - user_id (str): ID del usuario autenticado
        - policy_type (str, opcional): Tipo de póliza específica
        
        Salida esperada:
        {
            "success": bool,
            "data": [
                {
                    "policy_type": str,
                    "policy_number": str,
                    "coverage": float,
                    "premium": float,
                    "status": str,
                    "expiry_date": str
                }
            ]
        }
        """
        try:
            user_data = None
            for doc_id, data in self.users_db.items():
                if data["user_id"] == user_id:
                    user_data = data
                    break
            
            if not user_data:
                return {
                    "success": False,
                    "error": "AUTH_REQUIRED",
                    "message": "Usuario no autenticado"
                }
            
            policies = user_data.get("policies", [])
            
            # Filtrar por tipo si se especifica
            if policy_type:
                policies = [p for p in policies if policy_type.lower() in p["policy_type"].lower()]
            
            if not policies:
                return {
                    "success": True,
                    "data": [],
                    "message": "No se encontraron pólizas activas"
                }
            
            return {
                "success": True,
                "data": policies
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "SERVICE_UNAVAILABLE",
                "message": "Error al consultar pólizas"
            }