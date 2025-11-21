"""
Database Schemas for the SaaS landing

Each Pydantic model name maps to a MongoDB collection using its lowercase name:
- User -> "user"
- BlogPost -> "blogpost"
- ContactMessage -> "contactmessage"

These schemas are used for validation when creating documents.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Password hash (server-side)")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    role: str = Field("user", description="Role of the user")
    is_active: bool = Field(True, description="Active status")

class BlogPost(BaseModel):
    title: str
    slug: str = Field(..., description="URL-friendly slug")
    excerpt: Optional[str] = None
    content: str
    author_name: str
    tags: List[str] = []
    status: str = Field("published", description="draft|published")
    published_at: Optional[datetime] = None

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str
    subject: Optional[str] = None
