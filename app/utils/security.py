import hashlib
import hmac
import time
import secrets
from typing import Optional
from fastapi import HTTPException, Depends, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class TokenManager:
    """Manage API tokens with optional expiration."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def create_token(self, user_id: str, expires_in: Optional[int] = None) -> str:
        """Create a signed token."""
        timestamp = str(int(time.time()))
        expires = str(int(time.time() + expires_in)) if expires_in else ""
        
        payload = f"{user_id}:{timestamp}:{expires}"
        signature = hmac.new(
            self.secret_key,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload}:{signature}"
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a token and return user_id if valid."""
        try:
            parts = token.split(":")
            if len(parts) != 4:
                return None
            
            user_id, timestamp, expires, signature = parts
            payload = f"{user_id}:{timestamp}:{expires}"
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Check expiration
            if expires and int(expires) < time.time():
                return None
            
            return user_id
            
        except (ValueError, IndexError):
            return None

def create_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hmac.compare_digest(hash_api_key(api_key), hashed_key)

# Enhanced authentication dependency
def enhanced_auth(secret_token: str):
    """Enhanced authentication with better security."""
    
    def verify_credentials(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Simple token comparison (you can enhance this with TokenManager)
        if not hmac.compare_digest(credentials.credentials, secret_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return None
    
    return verify_credentials