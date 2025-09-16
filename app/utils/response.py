from typing import Any, Optional, Dict, List
from pydantic import BaseModel


class APIResponse(BaseModel):
    """
    Standard API Response Format
    
    This class provides a consistent response format for all API endpoints.
    It includes success status, message, and optional data payload.
    """
    success: bool
    message: str
    data: Optional[Any] = None
    meta: Optional[Any] = None

