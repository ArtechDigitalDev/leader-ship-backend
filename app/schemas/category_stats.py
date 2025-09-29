from typing import List, Optional
from pydantic import BaseModel, Field


class CategoryStats(BaseModel):
    """Individual category statistics"""
    category_name: str = Field(..., description="Category name (Clarity, Consistency, etc.)")
    total_weeks: int = Field(..., ge=0, description="Total number of weeks for this category")
    total_lessons: int = Field(..., ge=0, description="Total number of lessons for this category")
    
    class Config:
        from_attributes = True


class CategoryStatsSummary(BaseModel):
    """Summary of all categories with their statistics"""
    categories: List[CategoryStats] = Field(..., description="List of all categories with stats")
    total_categories: int = Field(..., description="Total number of categories")
    total_weeks_across_categories: int = Field(..., description="Total weeks across all categories")
    total_lessons_across_categories: int = Field(..., description="Total lessons across all categories")
    
    class Config:
        from_attributes = True
