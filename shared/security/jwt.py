"""JWT Token 工具"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from pydantic import ValidationError

from shared.config.settings import get_settings

settings = get_settings()


# JWT 配置
SECRET_KEY = getattr(settings, "jwt_secret_key", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "access_token_expire_minutes", 30)  # 30分钟
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "refresh_token_expire_days", 7)  # 7天


def create_access_token(subject: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    创建访问令牌

    Args:
        subject: Token 主体（通常是用户ID）
        additional_claims: 额外的声明信息

    Returns:
        str: JWT Token
    """
    if additional_claims is None:
        additional_claims = {}

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        **additional_claims
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """
    创建刷新令牌

    Args:
        subject: Token 主体（通常是用户ID）

    Returns:
        str: JWT Token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证 Token

    Args:
        token: JWT Token

    Returns:
        Optional[Dict]: 解码后的 Token 数据，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    验证 Token 并返回用户ID

    Args:
        token: JWT Token
        token_type: Token 类型（access 或 refresh）

    Returns:
        Optional[str]: 用户ID，验证失败返回 None
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # 检查 Token 类型
    if payload.get("type") != token_type:
        return None

    # 检查过期时间
    exp = payload.get("exp")
    if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
        return None

    return payload.get("sub")
