import os
import jwt


def validate_jwt(token):
    try:
        secret = os.getenv("JWT_SECRET", "mysupersecretkey")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        return decoded
    except Exception as e:
        print(f"JWT validation failed: {e}")
        return None