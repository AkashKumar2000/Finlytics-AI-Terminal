import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.utils.security import decode_access_token

logger = logging.getLogger("tenant_middleware")


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts tenant (org_id) from JWT and attaches it to request state.

    This provides an additional layer of tenant awareness. The primary enforcement
    is in the API route handlers via get_current_user → user.org_id scoping on
    every database query. This middleware logs the tenant context for observability.

    Multi-tenant flow:
    1. HTTP request arrives with Authorization: Bearer <jwt>
    2. This middleware decodes JWT → extracts org_id
    3. Attaches org_id to request.state.org_id
    4. Route handler uses get_current_user dep → user.org_id to scope all DB queries
    5. No data from Org A can ever leak to Org B
    """

    async def dispatch(self, request: Request, call_next):
        # Skip auth-related paths
        if request.url.path.startswith("/api/v1/auth") or request.url.path in ("/", "/health"):
            return await call_next(request)

        # Extract tenant from JWT if present
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            payload = decode_access_token(token)
            if payload:
                request.state.org_id = payload.get("org_id")
                request.state.user_id = payload.get("sub")
                request.state.user_role = payload.get("role")
                logger.debug(
                    f"Tenant context: org={request.state.org_id} "
                    f"user={request.state.user_id} role={request.state.user_role}"
                )

        response = await call_next(request)
        return response
