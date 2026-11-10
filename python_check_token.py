import base64
import json
from datetime import datetime, timezone

token = input("Paste your access token locally: ").strip()

parts = token.split(".")

if len(parts) != 3:
    print("This is not a standard JWT.")
    print("It may be an opaque ZITADEL access token.")
    raise SystemExit

payload = parts[1]
payload += "=" * (-len(payload) % 4)

claims = json.loads(base64.urlsafe_b64decode(payload))

print("\nTOKEN DETAILS")
print("----------------------")

print("Issuer:", claims.get("iss"))
print("Audience:", claims.get("aud"))
print("Subject:", claims.get("sub"))
print("Scope:", claims.get("scope"))

expiry = claims.get("exp")

if expiry:
    expiry_time = datetime.fromtimestamp(
        expiry, tz=timezone.utc
    )
    print("Expires:", expiry_time)
    print("Expired:", datetime.now(timezone.utc) >= expiry_time)