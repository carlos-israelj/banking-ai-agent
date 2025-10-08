"""
Gestión de seguridad, autenticación y privacidad.
"""
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from config.settings import (
    SESSION_TIMEOUT_MINUTES,
    MAX_FAILED_AUTH_ATTEMPTS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_MINUTES
)

class SecurityManager:
    """
    Gestiona todos los aspectos de seguridad del agente.
    """
    
    def __init__(self):
        self.sessions = {}  # session_token -> session_data
        self.failed_attempts = {}  # user_id -> count
        self.rate_limits = {}  # user_id -> request_data
        self.blocked_users = set()
    
    def create_session(self, user_id: str, user_data: Dict) -> str:
        """
        Crea una nueva sesión segura para un usuario autenticado.
        
        Returns:
            session_token: Token único de sesión
        """
        session_token = secrets.token_urlsafe(32)
        
        now = datetime.now()
        expiry = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        
        self.sessions[session_token] = {
            "user_id": user_id,
            "user_name": user_data.get('name', 'Usuario'),
            "document_id": user_data.get('document_id'),
            "created_at": now,
            "last_activity": now,
            "expires_at": expiry,
            "authenticated": True
        }
        
        # Reset failed attempts on successful auth
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]
        
        return session_token
    
    def validate_session(self, session_token: str) -> tuple[bool, Optional[Dict]]:
        """
        Valida si una sesión es válida y no ha expirado.
        
        Returns:
            (is_valid, session_data)
        """
        if not session_token or session_token not in self.sessions:
            return False, None
        
        session = self.sessions[session_token]
        now = datetime.now()
        
        # Verificar expiración
        if now > session["expires_at"]:
            del self.sessions[session_token]
            return False, None
        
        # Verificar timeout por inactividad
        time_inactive = now - session["last_activity"]
        if time_inactive > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            del self.sessions[session_token]
            return False, None
        
        # Actualizar última actividad
        session["last_activity"] = now
        
        return True, session
    
    def destroy_session(self, session_token: str) -> bool:
        """Destruye una sesión (logout)"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def record_failed_attempt(self, user_id: str) -> Dict:
        """
        Registra un intento fallido de autenticación.
        Bloquea al usuario si excede el máximo.
        
        Returns:
            {"blocked": bool, "attempts": int, "max_attempts": int}
        """
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = {
                "count": 0,
                "first_attempt": datetime.now()
            }
        
        self.failed_attempts[user_id]["count"] += 1
        attempts = self.failed_attempts[user_id]["count"]
        
        if attempts >= MAX_FAILED_AUTH_ATTEMPTS:
            self.blocked_users.add(user_id)
            return {
                "blocked": True,
                "attempts": attempts,
                "max_attempts": MAX_FAILED_AUTH_ATTEMPTS
            }
        
        return {
            "blocked": False,
            "attempts": attempts,
            "max_attempts": MAX_FAILED_AUTH_ATTEMPTS,
            "remaining": MAX_FAILED_AUTH_ATTEMPTS - attempts
        }
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Verifica si un usuario está bloqueado"""
        return user_id in self.blocked_users
    
    def check_rate_limit(self, user_id: str) -> Dict:
        """
        Implementa rate limiting para prevenir abuso.
        
        Returns:
            {"allowed": bool, "remaining": int, "reset_time": datetime}
        """
        now = datetime.now()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = {
                "count": 1,
                "window_start": now
            }
            return {
                "allowed": True,
                "remaining": RATE_LIMIT_REQUESTS - 1,
                "reset_time": now + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
            }
        
        rate_data = self.rate_limits[user_id]
        time_elapsed = now - rate_data["window_start"]
        
        # Reset si pasó la ventana de tiempo
        if time_elapsed > timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES):
            self.rate_limits[user_id] = {
                "count": 1,
                "window_start": now
            }
            return {
                "allowed": True,
                "remaining": RATE_LIMIT_REQUESTS - 1,
                "reset_time": now + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
            }
        
        # Incrementar contador
        rate_data["count"] += 1
        
        if rate_data["count"] > RATE_LIMIT_REQUESTS:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": rate_data["window_start"] + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
            }
        
        return {
            "allowed": True,
            "remaining": RATE_LIMIT_REQUESTS - rate_data["count"],
            "reset_time": rate_data["window_start"] + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
        }
    
    def sanitize_output(self, text: str, authenticated: bool) -> str:
        """
        Filtra información sensible de las respuestas.
        """
        if not authenticated:
            # Ocultar números de cuenta (10 dígitos)
            text = re.sub(r'\b\d{10}\b', '****', text)
            
            # Ocultar números de tarjeta (16 dígitos con posibles espacios/guiones)
            text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                         '**** **** **** ****', text)
            
            # Ocultar cédulas (10 dígitos Ecuador)
            text = re.sub(r'\b\d{10}\b', '****', text)
            
            # Ocultar montos grandes
            text = self._mask_large_amounts(text)
        
        return text
    
    def _mask_large_amounts(self, text: str) -> str:
        """Enmascara montos de dinero grandes"""
        pattern = r'\$[\d,]+\.\d{2}'
        
        def mask_if_large(match):
            amount_str = match.group(0).replace('$', '').replace(',', '')
            try:
                amount = float(amount_str)
                if amount > 1000:
                    return '$****'
                return match.group(0)
            except:
                return match.group(0)
        
        return re.sub(pattern, mask_if_large, text)
    
    def validate_input(self, user_input: str) -> Dict:
        """
        Valida la entrada del usuario para detectar intentos maliciosos.
        """
        # Patrones sospechosos
        suspicious_patterns = [
            (r'<script', 'XSS'),
            (r'javascript:', 'XSS'),
            (r'eval\(', 'Code Injection'),
            (r'exec\(', 'Code Injection'),
            (r'\bOR\b.*=.*', 'SQL Injection'),
            (r'UNION\s+SELECT', 'SQL Injection'),
            (r'DROP\s+TABLE', 'SQL Injection'),
            (r'--', 'SQL Comment'),
        ]
        
        for pattern, attack_type in suspicious_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    "valid": False,
                    "reason": f"Patrón sospechoso detectado: {attack_type}"
                }
        
        # Validar longitud
        if len(user_input) > 2000:
            return {
                "valid": False,
                "reason": "Mensaje demasiado largo"
            }
        
        # Validar caracteres
        if len(user_input.strip()) == 0:
            return {
                "valid": False,
                "reason": "Mensaje vacío"
            }
        
        return {"valid": True}
    
    def log_security_event(self, event_type: str, user_id: str, 
                          details: Dict) -> None:
        """
        Registra eventos de seguridad para auditoría.
        En producción: enviar a sistema de logging centralizado.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        
        # En producción: CloudWatch, Datadog, Splunk, etc.
        print(f"[SECURITY] {log_entry}")
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash de datos sensibles para logging seguro"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_session_info(self, session_token: str) -> Optional[Dict]:
        """Obtiene información de una sesión sin datos sensibles"""
        is_valid, session = self.validate_session(session_token)
        if not is_valid:
            return None
        
        now = datetime.now()
        time_remaining = session["expires_at"] - now
        
        return {
            "user_name": session["user_name"],
            "authenticated": session["authenticated"],
            "minutes_remaining": int(time_remaining.total_seconds() / 60),
            "last_activity": session["last_activity"].strftime("%H:%M:%S")
        }