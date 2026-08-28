from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from .config import settings


@dataclass(frozen=True)
class RequestContext:
    workspace_id: str
    actor: str
    role: str


async def get_context(
    workspace_id: str = Header(default="demo", alias="X-Workspace-ID"),
    actor: str = Header(default="demo.approver", alias="X-Actor"),
    role: str = Header(default="approver", alias="X-Role"),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> RequestContext:
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not workspace_id.replace("-", "").isalnum() or len(workspace_id) > 80:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workspace id")
    if not actor.strip() or len(actor) > 120:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid actor")
    if role not in {"requester", "approver", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role")
    return RequestContext(workspace_id=workspace_id, actor=actor.strip(), role=role)


def require_approver(context: RequestContext = Depends(get_context)) -> RequestContext:
    if context.role not in {"approver", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approver role required")
    return context
