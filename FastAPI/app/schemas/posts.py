from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr

class Post(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    userId: int
    title: str
    body: str

class Comment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    postId: int
    name: str
    email: EmailStr
    body: str

class PostWithComments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    post: Post
    comments: list[Comment]
    comments_count: int
