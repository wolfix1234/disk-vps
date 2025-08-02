import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..utils.auth import authorized
from ..utils.file import allowed_file, save_image, secure_filename
from ..utils.path import safe_path
from ..utils.validation import validate_id, sanitize_filename
from ..config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()
config = Config()

@router.post('/upload/image')
async def upload_image(
    store_id: str = Form(..., alias='storeId'),
    file: UploadFile = File(...),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Upload an image to a store's image directory."""
    
    if not store_id or not file:
        raise HTTPException(status_code=400, detail="Missing storeId or file")
    
    validate_id(store_id)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")
    
    # Check file size (FastAPI handles this automatically with max_size, but we'll check manually)
    content = await file.read()
    if len(content) > config.MAX_CONTENT_LENGTH:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Reset file position for later use
    await file.seek(0)
    
    filename = sanitize_filename(file.filename)
    if not filename or not allowed_file(filename):
        raise HTTPException(status_code=400, detail="Invalid filename or file type")
    
    store_path = safe_path(config.UPLOAD_FOLDER, store_id)
    
    if not os.path.exists(store_path):
        raise HTTPException(status_code=404, detail=f"Store ID {store_id} does not exist")
    
    full_path = os.path.join(store_path, 'image', filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    success, error = await save_image(file, full_path)
    if not success:
        logger.error(f"Error saving image for store_id {store_id}: {error}")
        raise HTTPException(status_code=500, detail=f"Error saving image: {error}")
    
    logger.info(f"Image uploaded successfully for store_id: {store_id}, filename: {filename}")
    return {
        "message": "Image uploaded successfully",
        "path": f"{store_id}/image/{filename}",
        "storeId": store_id,
        "filename": filename,
        "size": os.path.getsize(full_path)
    }


@router.get("/images")
def get_image_names(
    store_id: str = Header(..., alias='storeId'),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """List all images in a store's image directory."""

    if not store_id:
        raise HTTPException(status_code=400, detail="Missing storeId in headers")

    validate_id(store_id)

    store_path = safe_path(config.UPLOAD_FOLDER, store_id)

    if not os.path.exists(store_path):
        raise HTTPException(status_code=404, detail=f"Store ID {store_id} does not exist")

    image_path = os.path.join(store_path, "image")
    try:
        image_files = [f for f in os.listdir(image_path) if allowed_file(f)]
        logger.info(f"Listed images for store_id: {store_id}")
        return {"images": image_files}
    except Exception as e:
        logger.error(f"Error listing images for store_id {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading images for {store_id}")


class DeleteImageRequest(BaseModel):
    storeId: str
    filename: str

@router.delete("/delete/image")
def delete_image(
    request: DeleteImageRequest,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Delete an image from a store's image directory."""

    store_id = request.storeId
    filename = request.filename

    if not all([store_id, filename]):
        raise HTTPException(status_code=400, detail="Missing storeId or filename")
    
    validate_id(store_id)
    
    filename = sanitize_filename(filename)
    if not filename or not allowed_file(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    store_path = safe_path(config.UPLOAD_FOLDER, store_id)

    file_path = os.path.join(store_path, "image", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        os.remove(file_path)
        logger.info(f"Deleted image: {file_path}")
        return {"message": "Image deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting image {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting image")
