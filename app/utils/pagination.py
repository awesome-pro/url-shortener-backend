from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field
from fastapi import Query
from math import ceil

# Generic type for paginated data
T = TypeVar('T')


class Pagination(BaseModel):
    """Pagination metadata following your TypeScript interface pattern"""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    has_next: bool = Field(..., description="Whether there is a next page")
    
    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "Pagination":
        """Create pagination metadata from basic parameters"""
        total_pages = ceil(total / limit) if total > 0 else 0
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_previous=page > 1,
            has_next=page < total_pages
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response that can be used with any data type"""
    data: List[T] = Field(..., description="The paginated data items")
    pagination: Pagination = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(cls, data: List[T], page: int, limit: int, total: int) -> "PaginatedResponse[T]":
        """Create a paginated response from data and pagination parameters"""
        pagination_meta = Pagination.create(page, limit, total)
        return cls(data=data, pagination=pagination_meta)


class PaginationParams(BaseModel):
    """Pagination parameters for API endpoints"""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: int = Field(20, ge=1, le=100, description="Number of items per page")
    
    @property
    def skip(self) -> int:
        """Calculate the number of items to skip for database queries"""
        return (self.page - 1) * self.limit


class PaginationQuery:
    """FastAPI dependency for pagination query parameters"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.limit = limit
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries"""
        return (self.page - 1) * self.limit
    
    def to_params(self) -> PaginationParams:
        """Convert to PaginationParams model"""
        return PaginationParams(page=self.page, limit=self.limit)


class CursorPagination(BaseModel):
    """Cursor-based pagination metadata for large datasets"""
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Whether there are more items")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    previous_cursor: Optional[str] = Field(None, description="Cursor for previous page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Generic cursor-based paginated response"""
    data: List[T] = Field(..., description="The paginated data items")
    pagination: CursorPagination = Field(..., description="Cursor pagination metadata")


# Utility functions for creating paginated responses
def create_paginated_response(
    data: List[Any], 
    page: int, 
    limit: int, 
    total: int
) -> Dict[str, Any]:
    """
    Create a paginated response dictionary (for backward compatibility)
    
    Args:
        data: List of items to paginate
        page: Current page number
        limit: Items per page
        total: Total number of items
        
    Returns:
        Dictionary with data and pagination metadata
    """
    pagination = Pagination.create(page, limit, total)
    return {
        "data": data,
        "pagination": pagination.model_dump()
    }


def paginate_query_result(
    items: List[Any],
    total_count: int,
    pagination_params: PaginationParams
) -> PaginatedResponse[Any]:
    """
    Create a PaginatedResponse from query results
    
    Args:
        items: The items returned from the database query
        total_count: Total count of items (from a separate count query)
        pagination_params: Pagination parameters
        
    Returns:
        PaginatedResponse with the items and pagination metadata
    """
    return PaginatedResponse.create(
        data=items,
        page=pagination_params.page,
        limit=pagination_params.limit,
        total=total_count
    )


# Legacy support - aliases for backward compatibility
PaginationInfo = Pagination  # Alias for existing code
PagedResponse = PaginatedResponse  # Alias for existing code

# Constants for pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1
