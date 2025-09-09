"""
FastAPI dependencies for pagination across different modules
"""
from typing import Annotated
from fastapi import Depends, Query

from app.utils.pagination import PaginationQuery, PaginationParams


# Standard pagination dependency
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page")
) -> PaginationParams:
    """
    FastAPI dependency to extract pagination parameters from query string.
    
    Usage:
        @app.get("/items")
        async def get_items(pagination: PaginationParams = Depends(get_pagination_params)):
            skip = pagination.skip
            # ... your logic here
    """
    return PaginationParams(page=page, limit=limit)


# Alternative dependency using PaginationQuery class
def get_pagination_query(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
) -> PaginationQuery:
    """
    FastAPI dependency that returns a PaginationQuery object.
    
    Usage:
        @app.get("/items")
        async def get_items(pagination: PaginationQuery = Depends(get_pagination_query)):
            skip = pagination.skip
            params = pagination.to_params()
    """
    return PaginationQuery(page=page, limit=limit)



# Type aliases for cleaner code
PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
PaginationQueryDep = Annotated[PaginationQuery, Depends(get_pagination_query)]
