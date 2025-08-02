from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional
import re

class StoreRequest(BaseModel):
    store_id: str = Field(..., min_length=1, max_length=50, description="Store identifier")
    
    @validator('store_id')
    def validate_store_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Store ID must contain only alphanumeric characters, underscores, and hyphens')
        return v

class JsonFileRequest(BaseModel):
    store_id: str = Field(..., min_length=1, max_length=50)
    filename: str = Field(..., min_length=1, max_length=100)
    
    @validator('store_id')
    def validate_store_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Store ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.endswith('.json'):
            raise ValueError('Filename must end with .json')
        clean_name = re.sub(r'[^a-zA-Z0-9._-]', '', v)
        if clean_name != v:
            raise ValueError('Filename contains invalid characters')
        return v

class JsonUpdateRequest(JsonFileRequest):
    data: Dict[str, Any] = Field(..., description="JSON data to update")

class ImageDeleteRequest(BaseModel):
    store_id: str = Field(..., min_length=1, max_length=50)
    filename: str = Field(..., min_length=1, max_length=100)
    
    @validator('store_id')
    def validate_store_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Store ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        allowed_extensions = {'.webp', '.png'}
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError('File must be .webp or .png')
        clean_name = re.sub(r'[^a-zA-Z0-9._-]', '', v)
        if clean_name != v:
            raise ValueError('Filename contains invalid characters')
        return v

class DynamicJsonRequest(BaseModel):
    store_id: str = Field(..., min_length=1, max_length=50)
    template_name: str = Field(..., min_length=1, max_length=50, description="Template name (without lg/sm suffix)")
    
    @validator('store_id')
    def validate_store_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Store ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('template_name')
    def validate_template_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Template name must contain only alphanumeric characters, underscores, and hyphens')
        return v