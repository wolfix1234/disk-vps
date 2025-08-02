import os
import shutil
from fastapi import APIRouter, Depends, Header, HTTPException
from ..utils.auth import authorized
from ..utils.path import safe_path
from ..config import Config

router = APIRouter()
config = Config()

@router.get("/init-store")
def init_store(
    store_id: str = Header(..., alias='storeId'),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Initialize a store by copying JSON templates into its directory."""
    if not store_id:
        raise HTTPException(status_code=400, detail="Missing storeId in header")

    store_path = safe_path(config.UPLOAD_FOLDER, store_id)

    store_json_path = os.path.join(store_path, "json")
    if os.path.exists(store_json_path):
        return {"message": "Store already exists"}

    try:
        os.makedirs(store_json_path, exist_ok=True)

        template_folder = config.TEMPLATE_FOLDER
        for filename in os.listdir(template_folder):
            if filename.endswith(".json"):
                src = os.path.join(template_folder, filename)
                dst = os.path.join(store_json_path, filename)
                shutil.copyfile(src, dst)

        vps_url = config.VPS_URL
        return {
            "message": "Store initialized with templates",
            "url": f"{vps_url}/{store_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize store: {str(e)}")
