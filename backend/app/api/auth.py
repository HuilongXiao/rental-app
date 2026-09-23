from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.core.config import SESSION_SECRET
from app.core.security import verify_password
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])
serializer = URLSafeTimedSerializer(SESSION_SECRET)
COOKIE_NAME = "rental_session"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    try:
        user_id = serializer.loads(token, max_age=60 * 60 * 24)
    except BadSignature as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    response.set_cookie(COOKIE_NAME, serializer.dumps(user.id), httponly=True, samesite="lax", secure=False, max_age=86400)
    return {
        "status": "ok",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "is_system": user.is_system,
        },
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "is_system": user.is_system,
    }
