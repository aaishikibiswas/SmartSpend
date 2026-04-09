from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from backend.storage import Storage

router = APIRouter()


class RegisterPayload(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginPayload(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class ProfileUpdatePayload(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    plan: str | None = Field(default=None, max_length=80)


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix) :].strip()
    return authorization.strip()


@router.post("/register")
def register(payload: RegisterPayload):
    try:
        user = Storage.create_user(payload.full_name, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session_token = Storage.create_session(user["id"])
    return {
        "status": 201,
        "data": {
            "user": user,
            "sessionToken": session_token,
        },
        "message": "Account created successfully.",
    }


@router.post("/login")
def login(payload: LoginPayload):
    user = Storage.authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    session_token = Storage.create_session(user["id"])
    return {
        "status": 200,
        "data": {
            "user": user,
            "sessionToken": session_token,
        },
        "message": "Logged in successfully.",
    }


@router.get("/me")
def get_me(authorization: Optional[str] = Header(default=None)):
    token = _extract_bearer_token(authorization)
    user = Storage.get_user_by_session(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return {
        "status": 200,
        "data": user,
    }


@router.put("/me")
def update_me(payload: ProfileUpdatePayload, authorization: Optional[str] = Header(default=None)):
    token = _extract_bearer_token(authorization)
    user = Storage.get_user_by_session(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    updated = Storage.update_user(
        user["id"],
        {
            "full_name": payload.full_name,
            "plan": payload.plan or user.get("plan", "Pro Plan"),
            "avatar_seed": user["email"].replace("@", "-"),
        },
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "status": 200,
        "data": updated,
        "message": "Profile updated successfully.",
    }


@router.post("/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    token = _extract_bearer_token(authorization)
    Storage.delete_session(token)
    return {
        "status": 200,
        "data": {"success": True},
        "message": "Logged out successfully.",
    }
