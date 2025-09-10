import uuid


def generate_uuid() -> str:
    """Generate a new UUID as a hex string."""
    return uuid.uuid4().hex


def generate_uuid_callable():
    """Callable function for SQLAlchemy default values."""
    return lambda: uuid.uuid4().hex
