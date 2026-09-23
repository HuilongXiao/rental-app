from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import INITIAL_ADMIN_PASSWORD, INITIAL_ADMIN_USERNAME, SESSION_SECRET
from app.core.security import verify_password
from app.db.seed import seed_system_data
from app.db.session import get_db
from app.models.user import User

app = FastAPI(title="Rental App API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    seed_system_data()


@app.post("/api/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return {
        "status": "ok",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "is_system": user.is_system,
        },
        "token": "dev-token",
    }


@app.get("/api/auth/me")
def me():
    return {"status": "ok", "service": "auth"}
