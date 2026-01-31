from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    message: str
    files: List[str] = [] # List of file paths returned by /upload


class ChatResponse(BaseModel):
    response: str
    
class SkillRequest(BaseModel):
    name: str
    description: str
    instructions: str
    
class SkillResponse(BaseModel):
    name: str
    description: str
    path: str
