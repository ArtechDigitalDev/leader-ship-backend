from typing import Any, Optional, Dict, List
from pydantic import BaseModel
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


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


class APIException(HTTPException):
    """
    Custom HTTPException that returns APIResponse format
    
    This class extends HTTPException to provide consistent error responses
    with success, message, and data fields.
    """
    
    def __init__(
        self,
        status_code: int,
        message: str,
        data: Optional[dict] = None,
        success: bool = False
    ):
        # Direct response without "detail" wrapper
        detail = {
            "success": success,
            "message": message,
            "data": data
        }
        super().__init__(status_code=status_code, detail=detail)


# Custom exception handler to remove "detail" wrapper
async def api_exception_handler(request: Request, exc: APIException):
    """Custom exception handler for APIException to remove detail wrapper"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

