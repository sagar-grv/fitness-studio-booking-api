"""Application configuration.

Values can be overridden with environment variables for deployment.
SECRET_KEY defaults to a development value - always set it in production.
"""

import os

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitness_studio.db")

# Timezone: all class times are stored in IST as required by the brief.
IST = "Asia/Kolkata"
