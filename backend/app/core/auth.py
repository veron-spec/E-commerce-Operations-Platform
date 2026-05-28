import re

import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Returns (is_valid, message)."""
    if len(password) < 8:
        return False, "密码长度至少 8 位"
    if not re.search(r"[A-Z]", password):
        return False, "密码需要包含至少一个大写字母"
    if not re.search(r"[a-z]", password):
        return False, "密码需要包含至少一个小写字母"
    if not re.search(r"\d", password):
        return False, "密码需要包含至少一个数字"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
        return False, "密码需要包含至少一个特殊字符"
    return True, ""


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
