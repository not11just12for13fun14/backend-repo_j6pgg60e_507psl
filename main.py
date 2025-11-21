import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from database import create_document, get_documents, db

app = FastAPI(title="SaaS Landing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Root and health
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "SaaS Landing Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
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
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# -----------------------------
# Pricing (static for now)
# -----------------------------
class Plan(BaseModel):
    id: str
    name: str
    price: str
    period: str
    features: List[str]
    cta: str
    popular: bool = False

@app.get("/api/pricing", response_model=List[Plan])
def get_pricing():
    return [
        Plan(
            id="starter",
            name="Starter",
            price="$0",
            period="/mo",
            features=[
                "Up to 3 projects",
                "Basic analytics",
                "Community support",
            ],
            cta="Get Started",
        ),
        Plan(
            id="pro",
            name="Pro",
            price="$19",
            period="/mo",
            features=[
                "Unlimited projects",
                "Advanced analytics",
                "Email support",
                "Automation rules",
            ],
            cta="Start Free Trial",
            popular=True,
        ),
        Plan(
            id="business",
            name="Business",
            price="$49",
            period="/mo",
            features=[
                "Everything in Pro",
                "Team seats (5)",
                "Priority support",
                "Audit logs",
            ],
            cta="Contact Sales",
        ),
    ]

# -----------------------------
# Auth (demo only - not secure)
# -----------------------------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    token: str

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(data: SignupRequest):
    # very simple demo: store email + password as password_hash (not secure)
    # check if user exists
    existing = get_documents("user", {"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = create_document(
        "user",
        {
            "name": data.name,
            "email": data.email,
            "password_hash": data.password,
            "avatar_url": None,
            "role": "user",
            "is_active": True,
        },
    )
    return AuthResponse(user_id=user_id, name=data.name, email=data.email, token=f"demo-{user_id}")

@app.post("/api/auth/login", response_model=AuthResponse)
def login(data: LoginRequest):
    users = get_documents("user", {"email": data.email, "password_hash": data.password})
    if not users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    u = users[0]
    return AuthResponse(user_id=str(u.get("_id")), name=u.get("name", "User"), email=u.get("email"), token=f"demo-{u.get('_id')}")

# -----------------------------
# Blog
# -----------------------------
class BlogCreate(BaseModel):
    title: str
    content: str
    author_name: str
    tags: Optional[List[str]] = []

class BlogItem(BaseModel):
    id: str
    title: str
    excerpt: Optional[str] = None
    content: str
    author_name: str
    slug: str
    published_at: datetime
    tags: List[str] = []

@app.get("/api/blog", response_model=List[BlogItem])
def list_blog():
    posts = get_documents("blogpost", {"status": {"$in": ["published", None]}})
    # seed minimal posts if empty
    if not posts:
        now = datetime.utcnow()
        for p in [
            {
                "title": "Introducing Our Fintech Toolkit",
                "excerpt": "A gentle, pastel-first UI kit for modern SaaS.",
                "content": "Build faster with elegant defaults and a clean API.",
                "author_name": "Team",
                "slug": "introducing-our-fintech-toolkit",
                "status": "published",
                "published_at": now,
                "tags": ["product", "design"],
            },
            {
                "title": "Designing with Pastels",
                "excerpt": "Why soft palettes convert better.",
                "content": "Pastel themes reduce cognitive load and feel premium.",
                "author_name": "Design",
                "slug": "designing-with-pastels",
                "status": "published",
                "published_at": now,
                "tags": ["design"],
            },
        ]:
            create_document("blogpost", p)
        posts = get_documents("blogpost", {"status": {"$in": ["published", None]}})

    items: List[BlogItem] = []
    for d in posts:
        items.append(
            BlogItem(
                id=str(d.get("_id")),
                title=d.get("title"),
                excerpt=d.get("excerpt"),
                content=d.get("content"),
                author_name=d.get("author_name", "Team"),
                slug=d.get("slug"),
                published_at=d.get("published_at") or datetime.utcnow(),
                tags=d.get("tags", []),
            )
        )
    return items

@app.post("/api/blog", response_model=BlogItem)
def create_blog(post: BlogCreate):
    slug = post.title.lower().replace(" ", "-")
    data = {
        "title": post.title,
        "excerpt": post.content[:140] + ("..." if len(post.content) > 140 else ""),
        "content": post.content,
        "author_name": post.author_name,
        "slug": slug,
        "status": "published",
        "published_at": datetime.utcnow(),
        "tags": post.tags or [],
    }
    post_id = create_document("blogpost", data)
    return BlogItem(id=post_id, **{k: data[k] for k in data})

# -----------------------------
# Contact form
# -----------------------------
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str
    subject: Optional[str] = None

class ContactResponse(BaseModel):
    ok: bool

@app.post("/api/contact", response_model=ContactResponse)
def submit_contact(data: ContactRequest):
    create_document(
        "contactmessage",
        {
            "name": data.name,
            "email": data.email,
            "message": data.message,
            "subject": data.subject,
            "status": "new",
            "received_at": datetime.utcnow(),
        },
    )
    return ContactResponse(ok=True)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
