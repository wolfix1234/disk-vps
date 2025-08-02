from pathlib import Path
from fastapi import HTTPException

def safe_path(base, *parts):
    try:
        base_path = Path(base).resolve()
        full_path = Path(base, *parts).resolve()
        if base_path not in full_path.parents and base_path != full_path:
            raise HTTPException(status_code=400, detail="Invalid path")
        return str(full_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path construction")