import os
# Supported database types by name
DB_TYPE = "cloud-sql-postgres"

# Supported authentication providers by name
GOOGLE = "google-oidc"
AZURE = "azure-oidc"

# Selected database type to use
DATABASE_TYPE = DB_TYPE

# Google login
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"



if "INSTANCE_CONNECTION_NAME" in os.environ:
    FRONTEND_URL = "https://mal-6wcv5jbs7a-nw.a.run.app"
else:
    FRONTEND_URL = "http://localhost:8080"
GOOGLE_REDIRECT_URL = f"{FRONTEND_URL}/api/google-login-callback/"
# Front end endpoint


# JWT access token configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", None)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
AUTH_TOKEN_EXPIRE_MINUTES = 1
