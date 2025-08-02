from fastapi import APIRouter
from . import stores, images, json_files

# Create the main v1 router
router = APIRouter(prefix="/api/v1")

# Include all route modules
router.include_router(stores.router)
router.include_router(images.router)
router.include_router(json_files.router)