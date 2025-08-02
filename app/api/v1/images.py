import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import List
from ...utils.auth import authorized
from ...utils.file import allowed_file, save_image, secure_filename
from ...utils.path import safe_path
from ...utils.validation import sanitize_filename
from ...config import Config
from ...models.requests import ImageDeleteRequest
from ...models.responses import ImageUploadResponse, ImageListResponse, BaseResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["images"])
config = Config()

@router.post(
    "/{store_id}/images",
    response_model=ImageUploadResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Upload an image to a store",
    description="Upload an image file (WebP or PNG) to a store's image directory"
)
async def upload_image(
    store_id: str,
    file: UploadFile = File(..., description="Image file to upload"),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Upload an image to a store's image directory."""
    
    # Validate store_id format
    if not store_id or not store_id.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid store ID format"
        )
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > config.MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Reset file position
    await file.seek(0)
    
    # Validate filename
    filename = sanitize_filename(file.filename)
    if not filename or not allowed_file(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename or file type. Only WebP and PNG files are allowed."
        )
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        
        if not os.path.exists(store_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store '{store_id}' does not exist"
            )
        
        # Create image directory if it doesn't exist
        image_dir = os.path.join(store_path, 'image')
        os.makedirs(image_dir, exist_ok=True)
        
        full_path = os.path.join(image_dir, filename)
        
        success, error = await save_image(file, full_path)
        if not success:
            logger.error(f"Error saving image for store {store_id}: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image: {error}"
            )
        
        file_size = os.path.getsize(full_path)
        logger.info(f"Image uploaded successfully for store {store_id}: {filename} ({file_size} bytes)")
        
        return ImageUploadResponse(
            message="Image uploaded successfully",
            path=f"{store_id}/image/{filename}",
            store_id=store_id,
            filename=filename,
            size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading image for store {store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/{store_id}/images",
    response_model=ImageListResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="List all images in a store",
    description="Get a list of all image files in a store's image directory"
)
async def list_images(
    store_id: str,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """List all images in a store's image directory."""
    
    # Validate store_id format
    if not store_id or not store_id.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid store ID format"
        )
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        
        if not os.path.exists(store_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store '{store_id}' does not exist"
            )
        
        image_path = os.path.join(store_path, "image")
        
        if not os.path.exists(image_path):
            # Return empty list if image directory doesn't exist yet
            return ImageListResponse(
                message="No images found",
                images=[]
            )
        
        image_files = [f for f in os.listdir(image_path) if allowed_file(f)]
        logger.info(f"Listed {len(image_files)} images for store {store_id}")
        
        return ImageListResponse(
            message=f"Found {len(image_files)} images",
            images=image_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing images for store {store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete(
    "/{store_id}/images/{filename}",
    response_model=BaseResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Delete an image from a store",
    description="Delete a specific image file from a store's image directory"
)
async def delete_image(
    store_id: str,
    filename: str,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Delete an image from a store's image directory."""
    
    # Validate using Pydantic model
    request = ImageDeleteRequest(store_id=store_id, filename=filename)
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, request.store_id)
        file_path = os.path.join(store_path, "image", request.filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is not a file"
            )
        
        os.remove(file_path)
        logger.info(f"Deleted image: {file_path}")
        
        return BaseResponse(message="Image deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )