import os
import shutil
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ...utils.auth import authorized
from ...utils.path import safe_path
from ...config import Config
from ...models.requests import StoreRequest
from ...models.responses import StoreInitResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["stores"])
config = Config()

@router.post(
    "/{store_id}/initialize",
    response_model=StoreInitResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Initialize a new store",
    description="Creates a new store directory and copies template JSON files"
)
async def initialize_store(
    store_id: str,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Initialize a store by copying JSON templates into its directory."""
    
    # Validate store_id
    request = StoreRequest(store_id=store_id)
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, request.store_id)
        store_json_path = os.path.join(store_path, "json")
        
        if os.path.exists(store_json_path):
            return StoreInitResponse(
                message="Store already exists",
                url=f"{config.VPS_URL}/{request.store_id}"
            )

        # Create directories
        os.makedirs(store_json_path, exist_ok=True)
        os.makedirs(os.path.join(store_path, "image"), exist_ok=True)

        # Copy template files
        template_folder = config.TEMPLATE_FOLDER
        copied_files = []
        
        for filename in os.listdir(template_folder):
            if filename.endswith(".json"):
                src = os.path.join(template_folder, filename)
                dst = os.path.join(store_json_path, filename)
                shutil.copyfile(src, dst)
                copied_files.append(filename)

        logger.info(f"Store {request.store_id} initialized with {len(copied_files)} template files")
        
        return StoreInitResponse(
            message=f"Store initialized with {len(copied_files)} template files",
            url=f"{config.VPS_URL}/{request.store_id}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize store {request.store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize store: {str(e)}"
        )