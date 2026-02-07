from functools import lru_cache
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConfigurationError


@lru_cache
def _mongo_uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017/sentinel_upload")


def get_mongo_client() -> AsyncIOMotorClient:
    # Lazy client creation; connect on first use.
    return AsyncIOMotorClient(_mongo_uri())


def get_db():
    client = get_mongo_client()
    try:
        # Preferred: database name in URI path (e.g. ...mongodb.net/sentinel_upload)
        return client.get_default_database()
    except ConfigurationError:
        # Fallback for URIs without db path.
        return client.get_database(os.getenv("MONGO_DB", "sentinel_upload"))
