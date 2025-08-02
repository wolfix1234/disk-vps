from fastapi import HTTPException, Depends, Header
from typing import Optional

def get_auth_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate authorization token from header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    parts = authorization.split()
    
    # Handle missing, malformed, or incorrect token
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    elif len(parts) == 1:
        token = parts[0]
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return token

def authorized(secret_token: str):
    """Dependency factory for authorization."""
    def check_auth(token: str = Depends(get_auth_token)) -> None:
        if token != secret_token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return None
    return check_auth
