from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# Create a security scheme for better OpenAPI integration
security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Enter your API token"
)

def get_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract and validate authorization token from header."""
    if not credentials:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return credentials.credentials

def authorized(secret_token: str):
    """Dependency factory for authorization."""
    def check_auth(token: str = Depends(get_auth_token)) -> None:
        if token != secret_token:
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return None
    return check_auth
