from fastapi import APIRouter, HTTPException
from firebase_admin import auth
from app.models.auth import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(user: User):
    try:
        user_record = auth.create_user(email=user.email, password=user.password)
        return {"message": "User registered successfully", "uid": user_record.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login_user(user: User):
    try:
        user = auth.get_user_by_email(user.email)
        return {"message": "User logged in successfully", "uid": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout_user():
    return {"message": "User logged out successfully"}
