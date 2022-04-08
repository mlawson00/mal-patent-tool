import os


# Supported database types by name
MONGO_DB = "mongodb"

# Supported authentication providers by name
GOOGLE = "google-oidc"
AZURE = "azure-oidc"

# Selected database type to use
DATABASE_TYPE = MONGO_DB


# Google login
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_REDIRECT_URL = "https://mal-6wcv5jbs7a-nw.a.run.app/api/google-login-callback/"

# Azure login
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", None)
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", None)
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID", "common")
AZURE_AUTHORITY = os.environ.get("AZURE_AUTHORITY", f"https://login.microsoftonline.com/{AZURE_TENANT_ID}")
AZURE_DISCOVERY_URL = f"{AZURE_AUTHORITY}/v2.0/.well-known/openid-configuration"
AZURE_REDIRECT_URL = "http://localhost:8000/azure-login-callback/"

# Front end endpoint
FRONTEND_URL = "https://mal-6wcv5jbs7a-nw.a.run.app"

# JWT access token configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", None)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
AUTH_TOKEN_EXPIRE_MINUTES = 1
