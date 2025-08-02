from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class BaseResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

class StoreInitResponse(BaseResponse):
    url: str = Field(..., description="Store URL")

class ImageUploadResponse(BaseResponse):
    path: str = Field(..., description="Relative path to uploaded image")
    store_id: str
    filename: str
    size: int = Field(..., description="File size in bytes")

class ImageListResponse(BaseResponse):
    images: List[str] = Field(..., description="List of image filenames")

class JsonListResponse(BaseResponse):
    json_files: List[str] = Field(..., description="List of JSON filenames")

class JsonContentResponse(BaseResponse):
    data: Dict[str, Any] = Field(..., description="JSON file content")

class DynamicJsonResponse(BaseResponse):
    created_files: List[str] = Field(..., description="List of created files")

class DynamicJsonDeleteResponse(BaseResponse):
    deleted_files: List[str] = Field(..., description="List of deleted files")
    not_found: List[str] = Field(default=[], description="List of files that were not found")