import jwt
import time

payload = {
    "service": "api",
    "exp": time.time() + 300
}

token = jwt.encode(payload, "mysupersecretkey", algorithm="HS256")

print(token)