import os
import re
import json
import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from ..utils.auth import authorized
from ..utils.path import safe_path
from ..config import Config

router = APIRouter()
logger = logging.getLogger(__name__)
config = Config()


# GET JSON file content
@router.get("/json")
def get_json(
    store_id: str = Header(..., alias='storeId'),
    filename: str = Header(...),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    logger.info(f"Raw store_id: {repr(store_id)}")
    logger.info(f"Raw filename: {repr(filename)}")

    if not store_id or not filename:
        raise HTTPException(status_code=400, detail="Missing storeId or filename")

    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename.strip())

    if not store_id or not filename:
        raise HTTPException(status_code=400, detail="Invalid storeId or filename after sanitization")

    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        full_path = os.path.join(store_path, "json", filename)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path construction")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise HTTPException(status_code=400, detail="File is empty")
            f.seek(0)
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reading file")

# POST JSON file content
@router.post("/json")
def update_json(
    request: Dict[str, Any],
    store_id: str = Header(..., alias='storeId'),
    filename: str = Header(...),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    logger.info(f"Raw store_id: {repr(store_id)}")
    logger.info(f"Raw filename: {repr(filename)}")

    if not store_id or not filename:
        raise HTTPException(status_code=400, detail="Missing storeId or filename")

    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename.strip())

    if not store_id or not filename:
        raise HTTPException(status_code=400, detail="Invalid storeId or filename after sanitization")

    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        full_path = os.path.join(store_path, "json", filename)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path construction")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    new_data = request
    try:
        json.dumps(new_data)  # Ensure serializable
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        temp_path = f"{full_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2)
        os.replace(temp_path, full_path)
        return {"message": "File updated successfully"}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Error updating file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating file")


# List all JSON files in a store
@router.get("/list-json")
def list_json(
    store_id: str = Header(..., alias='storeId'),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    if not store_id:
        raise HTTPException(status_code=400, detail="Missing storeId header")

    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        json_path = os.path.join(store_path, "json")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path construction")

    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Store ID does not exist")

    try:
        json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
        return {"json_files": json_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON files: {str(e)}")


# Create dynamic JSON files
@router.post("/create-json")
def create_json(
    store_id: str = Header(..., alias='storeId'),
    dynamic: str = Header(..., alias='filename'),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    logger.info(f"Raw store_id: {repr(store_id)}")
    logger.info(f"Raw dynamic: {repr(dynamic)}")

    if not store_id or not dynamic:
        raise HTTPException(status_code=400, detail="Missing storeId or filename")

    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    dynamic = re.sub(r'[^a-zA-Z0-9._-]', '', dynamic.strip())

    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        lg_path = os.path.join(store_path, "json", f"{dynamic}lg.json")
        sm_path = os.path.join(store_path, "json", f"{dynamic}sm.json")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path construction")

    if os.path.isfile(lg_path) or os.path.isfile(sm_path):
        raise HTTPException(status_code=409, detail="File already exists")

    default_content = {
        "children": {
            "type": f"{dynamic}",
            "metaData": {
                "title": f"{dynamic}",
                "description": f"{dynamic} page"
            },
            "sections": [],
            "order": []
        }
    }

    def write_file(path):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = f"{path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(default_content, f, indent=2)
            os.replace(tmp, path)
            return True, None
        except Exception as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            return False, str(e)

    ok_lg, err_lg = write_file(lg_path)
    ok_sm, err_sm = write_file(sm_path)

    if ok_lg and ok_sm:
        return {"message": f"{dynamic}lg.json and {dynamic}sm.json created"}
    raise HTTPException(status_code=500, detail={
        "error": "File creation failed",
        "lg_error": err_lg,
        "sm_error": err_sm
    })

# Delete dynamic JSON files
@router.delete("/create-json")
def delete_json(
    store_id: str = Header(..., alias='storeId'),
    dynamic: str = Header(..., alias='filename'),
    _: None = Depends(authorized(config.SECRET_TOKEN))
):
    logger.info(f"Raw store_id: {repr(store_id)}")
    logger.info(f"Raw dynamic: {repr(dynamic)}")

    if not store_id or not dynamic:
        raise HTTPException(status_code=400, detail="Missing storeId or filename")

    store_id = re.sub(r'[^a-zA-Z0-9._-]', '', store_id.strip())
    dynamic = re.sub(r'[^a-zA-Z0-9._-]', '', dynamic.strip())

    try:
        store_path = safe_path(config.UPLOAD_FOLDER, store_id)
        lg_path = os.path.join(store_path, "json", f"{dynamic}lg.json")
        sm_path = os.path.join(store_path, "json", f"{dynamic}sm.json")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path construction")

    deleted = []
    not_found = []

    for path in [lg_path, sm_path]:
        if os.path.isfile(path):
            try:
                os.remove(path)
                deleted.append(os.path.basename(path))
                logger.info(f"Deleted: {path}")
            except Exception as e:
                logger.error(f"Delete failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Delete failed: {os.path.basename(path)}")
        else:
            not_found.append(os.path.basename(path))

    if deleted:
        return {
            "message": f"Deleted: {', '.join(deleted)}",
            "not_found": not_found
        }
    raise HTTPException(status_code=404, detail="No files found to delete")
