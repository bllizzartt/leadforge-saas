from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class TenantContext:
    """Thread-local tenant context for request lifecycle"""
    company_id: Optional[int] = None
    user_id: Optional[int] = None
    
    def set(self, company_id: int, user_id: int):
        self.company_id = company_id
        self.user_id = user_id
    
    def clear(self):
        self.company_id = None
        self.user_id = None
    
    @property
    def is_set(self) -> bool:
        return self.company_id is not None


tenant_context = TenantContext()


def get_current_tenant_id() -> int:
    """Get current tenant ID from context"""
    if not tenant_context.is_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not set"
        )
    return tenant_context.company_id


def get_current_user_id() -> int:
    """Get current user ID from context"""
    if not tenant_context.is_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not set"
        )
    return tenant_context.user_id


class TenantMiddleware:
    """Middleware to set tenant context from JWT token"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Import here to avoid circular imports
        from app.main import get_async_session
        from jose import jwt, JWTError
        from app.core.config import settings
        
        try:
            # Get Authorization header
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    payload = jwt.decode(
                        token, 
                        settings.SECRET_KEY, 
                        algorithms=["HS256"]
                    )
                    tenant_context.company_id = payload.get("company_id")
                    tenant_context.user_id = payload.get("user_id")
                except JWTError:
                    pass  # No valid token, continue without tenant context
        except Exception:
            pass  # Any error, continue without tenant context
        
        await self.app(scope, receive, send)


def require_role(allowed_roles: list[str]):
    """Decorator to require specific roles"""
    def role_checker(func: Callable):
        async def wrapper(*args, **kwargs):
            from app.models.company import UserRole
            from app.core.security import get_current_user
            
            user = await get_current_user()
            if user.role not in allowed_roles and user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return role_checker
