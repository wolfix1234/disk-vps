import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "run:app", 
        host="0.0.0.0", 
        port=5002, 
        reload=True,
        log_level="info",
        access_log=True
    )
    
    