"""
Database-agnostic types for cross-database compatibility.

Provides type decorators that work with both PostgreSQL (production)
and SQLite (testing), following Andrew Ng's "Build it right" methodology.
"""
import uuid
import json
from sqlalchemy import TypeDecorator, CHAR, String, Text
from sqlalchemy.dialects.postgresql import (
    UUID as PostgreSQL_UUID,
    JSONB as PostgreSQL_JSONB,
)


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36), storing as stringified hex values.

    This allows models to work with both PostgreSQL (production)
    and SQLite (testing) without modification.

    Following Andrew Ng's methodology:
    - Build it right: One type definition works everywhere
    - Test everything: Enables comprehensive testing with SQLite
    - Think about the future: Easy to extend for other databases
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            # SQLite and others: use CHAR(36)
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Convert Python UUID to database representation."""
        if value is None:
            return value
        elif dialect.name == "postgresql":
            # PostgreSQL handles UUID objects natively
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        else:
            # SQLite: store as string
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                # Assume it's already a string UUID
                return str(uuid.UUID(value))  # Validate format

    def process_result_value(self, value, dialect):
        """Convert database representation to Python UUID."""
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return value
        else:
            return uuid.UUID(value)


class JSON(TypeDecorator):
    """
    Platform-independent JSON type.

    Uses PostgreSQL's JSONB type when available, otherwise uses
    Text with JSON serialization.

    This allows models to work with both PostgreSQL (production)
    and SQLite (testing) without modification.

    Following Andrew Ng's methodology:
    - Build it right: One type definition works everywhere
    - Test everything: Enables comprehensive testing with SQLite
    - Think about the future: Easy to extend for other databases
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQL_JSONB())
        else:
            # SQLite and others: use Text
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        """Convert Python dict/list to database representation."""
        if value is None:
            return value
        elif dialect.name == "postgresql":
            # PostgreSQL handles JSON objects natively
            return value
        else:
            # SQLite: serialize to JSON string
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Convert database representation to Python dict/list."""
        if value is None:
            return value
        elif dialect.name == "postgresql":
            # PostgreSQL returns dict/list directly
            return value
        else:
            # SQLite: deserialize from JSON string
            return json.loads(value) if value else None
