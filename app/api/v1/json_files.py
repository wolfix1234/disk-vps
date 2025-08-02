import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict
from ...utils.auth import authorized
from ...utils.path import safe_path
from ...config import Config
from ...models.requests import JsonFileRequest, JsonUpdateRequest, DynamicJsonRequest
from ...models.responses import (
    JsonListResponse, JsonContentResponse, BaseResponse, 
    DynamicJsonResponse, DynamicJsonDeleteResponse, ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["json-files"])
config = Config()

@router.get(
    "/{store_id}/json",
    response_model=JsonListResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="List all JSON files in a store",
    description="Get a list of all JSON files in a store's json directory"
)
async def list_json_files(
    store_id: str,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """List all JSON files in a store."""
    
    # Validate store_id format
    if not store_id or not store_id.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid store ID format"
        )
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        json_path = os.path.join(store_path, "json")
        
        if not os.path.exists(json_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store '{store_id}' does not exist"
            )
        
        json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
        
        return JsonListResponse(
            message=f"Found {len(json_files)} JSON files",
            json_files=json_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing JSON files for store {store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/{store_id}/json/{filename}",
    response_model=JsonContentResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get JSON file content",
    description="Retrieve the content of a specific JSON file from a store"
)
async def get_json_file(
    store_id: str,
    filename: str,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Get JSON file content."""
    
    # Validate using Pydantic model
    request = JsonFileRequest(store_id=store_id, filename=filename)
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, request.store_id)
        full_path = os.path.join(store_path, "json", request.filename)
        
        if not os.path.isfile(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JSON file not found"
            )
        
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File is empty"
                )
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON format: {str(e)}"
                )
        
        return JsonContentResponse(
            message="JSON file retrieved successfully",
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading JSON file {request.filename} for store {request.store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put(
    "/{store_id}/json/{filename}",
    response_model=BaseResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Update JSON file content",
    description="Update the content of a specific JSON file in a store"
)
async def update_json_file(
    store_id: str,
    filename: str,
    data: Dict[str, Any],
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Update JSON file content."""
    
    # Validate using Pydantic model
    request = JsonUpdateRequest(store_id=store_id, filename=filename, data=data)
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, request.store_id)
        full_path = os.path.join(store_path, "json", request.filename)
        
        if not os.path.isfile(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JSON file not found"
            )
        
        # Ensure data is serializable
        try:
            json.dumps(request.data)
        except (TypeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data is not JSON serializable: {str(e)}"
            )
        
        # Write to temporary file first, then replace
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        temp_path = f"{full_path}.tmp"
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(request.data, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_path, full_path)
            
            return BaseResponse(message="JSON file updated successfully")
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating JSON file {request.filename} for store {request.store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{store_id}/json/templates",
    response_model=DynamicJsonResponse,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Create dynamic JSON template files",
    description="Create a pair of JSON template files (lg and sm versions) for a store"
)
async def create_dynamic_json(
    store_id: str,
    request: DynamicJsonRequest,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Create dynamic JSON template files."""
    
    # Override store_id from path parameter
    request.store_id = store_id
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, request.store_id)
        lg_path = os.path.join(store_path, "json", f"{request.template_name}lg.json")
        sm_path = os.path.join(store_path, "json", f"{request.template_name}sm.json")
        
        # Check if files already exist
        if os.path.isfile(lg_path) or os.path.isfile(sm_path):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Template files already exist"
            )
        
        # Default template content
        default_content = {
            "children": {
                "type": request.template_name,
                "metaData": {
                    "title": request.template_name,
                    "description": f"{request.template_name} page"
                },
                "sections": [],
                "order": []
            }
        }
        
        created_files = []
        
        # Create both files
        for path, suffix in [(lg_path, "lg"), (sm_path, "sm")]:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                temp_path = f"{path}.tmp"
                
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, indent=2, ensure_ascii=False)
                
                os.replace(temp_path, path)
                created_files.append(f"{request.template_name}{suffix}.json")
                
            except Exception as e:
                # Clean up any created files on error
                for created_path in [lg_path, sm_path]:
                    if os.path.exists(created_path):
                        os.remove(created_path)
                    temp_created_path = f"{created_path}.tmp"
                    if os.path.exists(temp_created_path):
                        os.remove(temp_created_path)
                raise e
        
        logger.info(f"Created dynamic JSON templates for store {request.store_id}: {created_files}")
        
        return DynamicJsonResponse(
            message=f"Created {len(created_files)} template files",
            created_files=created_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dynamic JSON for store {request.store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete(
    "/{store_id}/json/templates/{template_name}",
    response_model=DynamicJsonDeleteResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Delete dynamic JSON template files",
    description="Delete a pair of JSON template files (lg and sm versions) from a store"
)
async def delete_dynamic_json(
    store_id: str,
    template_name: str,
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    """Delete dynamic JSON template files."""
    
    # Validate using Pydantic model
    request = DynamicJsonRequest(store_id=store_id, template_name=template_name)
    
    try:
        store_path = safe_path(config.UPLOAD_FOLDER, request.store_id)
        lg_path = os.path.join(store_path, "json", f"{request.template_name}lg.json")
        sm_path = os.path.join(store_path, "json", f"{request.template_name}sm.json")
        
        deleted_files = []
        not_found = []
        
        for path in [lg_path, sm_path]:
            filename = os.path.basename(path)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    deleted_files.append(filename)
                    logger.info(f"Deleted: {path}")
                except Exception as e:
                    logger.error(f"Failed to delete {path}: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to delete {filename}"
                    )
            else:
                not_found.append(filename)
        
        if not deleted_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No template files found to delete"
            )
        
        return DynamicJsonDeleteResponse(
            message=f"Deleted {len(deleted_files)} template files",
            deleted_files=deleted_files,
            not_found=not_found
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dynamic JSON for store {request.store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )