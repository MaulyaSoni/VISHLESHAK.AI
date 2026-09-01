"""
Week 3: Authentication API for FastAPI
Provides login, register, and user management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app_modules.auth.auth_manager import AuthManager
from app_modules.database.db_manager import DatabaseManager

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize auth manager
auth_manager = AuthManager()

# ─── Request/Response Models ─────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    message: str
    user: dict

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

# ─── Endpoints ───────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with email and password
    Returns session token and user info
    """
    try:
        from app_modules.auth.auth_manager import AuthError
        
        # Login user
        user, token = auth_manager.login_user(
            email=request.email,
            password=request.password
        )
        
        return LoginResponse(
            token=token,
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }
        )
    except AuthError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """
    Register new user
    Returns success message and user info
    """
    try:
        from app_modules.auth.auth_manager import AuthError
        
        # Register user
        user = auth_manager.register_user(
            email=request.email,
            username=request.username,
            password=request.password
        )
        
        # Auto-login after registration
        _, token = auth_manager.login_user(
            email=request.email,
            password=request.password
        )
        
        return RegisterResponse(
            message="User registered successfully",
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }
        )
    except AuthError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current user profile
    Requires Bearer token in Authorization header
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify session
        user = auth_manager.verify_session(token)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """
    Logout (client-side token removal)
    """
    return {"message": "Logged out successfully"}
