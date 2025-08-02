# 🚀 Simple API Usage Guide

## ✅ **Everything is Working Now!**

All middleware and CORS issues have been resolved. The API is now clean and simple.

## 🔑 **Authentication**

All API endpoints require this header:
```
Authorization: Bearer mamad
```

## 📚 **Documentation**

- **Swagger UI**: http://localhost:5002/docs
- **ReDoc**: http://localhost:5002/redoc
- **Health Check**: http://localhost:5002/health

## 🛠️ **PowerShell Examples (Windows)**

### Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:5002/health" -Method GET
```

### Initialize Store
```powershell
Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/my-store/initialize" -Method POST -Headers @{"Authorization"="Bearer mamad"}
```

### List JSON Files
```powershell
Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/my-store/json" -Method GET -Headers @{"Authorization"="Bearer mamad"}
```

### Get JSON File
```powershell
Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/my-store/json/homelg.json" -Method GET -Headers @{"Authorization"="Bearer mamad"}
```

### Update JSON File
```powershell
$data = @{
    children = @{
        type = "home"
        metaData = @{
            title = "My Updated Page"
            description = "Updated via API"
        }
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/my-store/json/homelg.json" -Method PUT -Headers @{"Authorization"="Bearer mamad"; "Content-Type"="application/json"} -Body $data
```

### List Images
```powershell
Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/my-store/images" -Method GET -Headers @{"Authorization"="Bearer mamad"}
```

## 🐚 **Bash/curl Examples (Linux/Mac/Git Bash)**

### Health Check
```bash
curl http://localhost:5002/health
```

### Initialize Store
```bash
curl -X POST "http://localhost:5002/api/v1/stores/my-store/initialize" \
  -H "Authorization: Bearer mamad"
```

### List JSON Files
```bash
curl -X GET "http://localhost:5002/api/v1/stores/my-store/json" \
  -H "Authorization: Bearer mamad"
```

### Get JSON File
```bash
curl -X GET "http://localhost:5002/api/v1/stores/my-store/json/homelg.json" \
  -H "Authorization: Bearer mamad"
```

### Update JSON File
```bash
curl -X PUT "http://localhost:5002/api/v1/stores/my-store/json/homelg.json" \
  -H "Authorization: Bearer mamad" \
  -H "Content-Type: application/json" \
  -d '{
    "children": {
      "type": "home",
      "metaData": {
        "title": "Updated Title",
        "description": "Updated via curl"
      }
    }
  }'
```

## 🎯 **Swagger UI Usage**

1. **Open**: http://localhost:5002/docs
2. **Click**: 🔒 **Authorize** button
3. **Enter**: `mamad` (just the token, no "Bearer")
4. **Click**: **Authorize** then **Close**
5. **Test**: Any endpoint will now work!

## 📋 **Available Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/stores/{store_id}/initialize` | Initialize store |
| GET | `/api/v1/stores/{store_id}/json` | List JSON files |
| GET | `/api/v1/stores/{store_id}/json/{filename}` | Get JSON file |
| PUT | `/api/v1/stores/{store_id}/json/{filename}` | Update JSON file |
| GET | `/api/v1/stores/{store_id}/images` | List images |
| POST | `/api/v1/stores/{store_id}/images` | Upload image |
| DELETE | `/api/v1/stores/{store_id}/images/{filename}` | Delete image |
| POST | `/api/v1/stores/{store_id}/json/templates` | Create template |
| DELETE | `/api/v1/stores/{store_id}/json/templates/{name}` | Delete template |

## 🔧 **Quick Test**

Run this to test everything:

```powershell
# Test health
Invoke-RestMethod -Uri "http://localhost:5002/health" -Method GET

# Test API with auth
Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/test/initialize" -Method POST -Headers @{"Authorization"="Bearer mamad"}

# List files
Invoke-RestMethod -Uri "http://localhost:5002/api/v1/stores/test/json" -Method GET -Headers @{"Authorization"="Bearer mamad"}
```

## ✅ **What's Fixed**

- ✅ No more middleware issues
- ✅ No more CORS problems
- ✅ Swagger UI works perfectly
- ✅ All endpoints accessible
- ✅ Clean, simple responses
- ✅ Easy development and testing

## 🚀 **Start Server**

```bash
python run.py
```

**That's it! Your API is now working perfectly! 🎉**
