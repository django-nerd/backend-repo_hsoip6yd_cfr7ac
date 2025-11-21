import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Design Lighting API running"}


# ---------- Schemas for request bodies ----------
class ContactIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=30)
    message: str = Field(..., min_length=10, max_length=2000)


# ---------- Helpers ----------
def serialize_product(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id")),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "price": doc.get("price"),
        "category": doc.get("category"),
        "in_stock": doc.get("in_stock", True),
        "image_url": doc.get("image_url"),
    }


# ---------- Routes ----------
@app.get("/api/products")
def list_products(category: Optional[str] = None, limit: int = 24):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    filt = {"category": category} if category else {}
    docs = get_documents("product", filt, limit=limit)
    return [serialize_product(d) for d in docs]


@app.get("/api/products/featured")
def featured_products(limit: int = 8):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    docs = get_documents("product", {}, limit=limit)
    return [serialize_product(d) for d in docs]


@app.post("/api/contact")
def submit_contact(payload: ContactIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc_id = create_document("contactin", payload)
    return {"status": "ok", "id": doc_id}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
