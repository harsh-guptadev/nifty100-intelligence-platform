import os
import json
from src.api.main import app

def generate_docs():
    os.makedirs("docs", exist_ok=True)
    
    # 1. Export OpenAPI spec
    openapi_schema = app.openapi()
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Exported docs/openapi.json")

    # 2. Export Postman Collection v2.1
    postman_items = []
    
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, details in methods.items():
            item_name = details.get("summary") or details.get("operationId") or f"{method.upper()} {path}"
            tag = details.get("tags", ["General"])[0]
            
            postman_item = {
                "name": item_name,
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": f"http://localhost:8000{path}",
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": [p for p in path.split("/") if p]
                    },
                    "description": details.get("description", "")
                },
                "response": []
            }
            
            # Find or create group/tag folder
            folder = next((f for f in postman_items if f["name"] == tag), None)
            if not folder:
                folder = {"name": tag, "item": []}
                postman_items.append(folder)
            folder["item"].append(postman_item)
            
    postman_collection = {
        "info": {
            "name": "Nifty 100 Financial Intelligence REST API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Collection of all 16 endpoints for the Nifty 100 Financial Intelligence Platform."
        },
        "item": postman_items
    }
    
    with open("docs/postman_collection.json", "w") as f:
        json.dump(postman_collection, f, indent=2)
    print("Exported docs/postman_collection.json")

if __name__ == "__main__":
    generate_docs()
