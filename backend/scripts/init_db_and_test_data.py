#!/usr/bin/env python3
"""
Initialize database and create test data.

This script:
1. Creates all database tables using SQLAlchemy
2. Creates test student and teacher accounts
3. Creates sample topics and interests
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.progress import Topic
from app.models.interest import Interest
from app.core.security import get_password_hash
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def init_database():
    """Create all database tables."""
    logger.info("Initializing database schema...")

    # Import all models to ensure they're registered with Base
    from app.models import user, interest, content, class_model, progress

    # Drop all existing tables first (for clean initialization)
    logger.info("Dropping existing tables if any...")
    try:
        # Use CASCADE to drop tables with dependencies
        from sqlalchemy import text
        with engine.begin() as conn:
            # Drop all tables with CASCADE
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO vividly"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        logger.info("✓ Existing schema dropped and recreated")
    except Exception as e:
        logger.warning(f"Could not drop schema (might not exist): {e}")
        logger.info("Continuing with table creation...")

    # Create all tables
    logger.info("Creating fresh database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created successfully")


def create_test_users(db):
    """Create test student and teacher accounts."""
    logger.info("Creating test users...")

    import uuid
    from app.models.user import UserRole, UserStatus

    test_users = [
        {
            "user_id": str(uuid.uuid4()),
            "email": "student1@test.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "Student",
            "role": UserRole.STUDENT,
            "status": UserStatus.ACTIVE,
            "grade_level": 8
        },
        {
            "user_id": str(uuid.uuid4()),
            "email": "teacher1@test.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "Teacher",
            "role": UserRole.TEACHER,
            "status": UserStatus.ACTIVE
        }
    ]

    created_users = []
    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            logger.info(f"  - User {user_data['email']} already exists, skipping")
            created_users.append(existing_user)
            continue

        # Create new user
        password = user_data.pop("password")
        password_hash = get_password_hash(password)

        user = User(**user_data, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)

        created_users.append(user)
        logger.info(f"  ✓ Created {user.role}: {user.email} (password: password123)")

    return created_users


def create_sample_topics(db):
    """Create sample educational topics."""
    logger.info("Creating sample topics...")

    sample_topics = [
        {
            "topic_id": "photosynthesis",
            "name": "Photosynthesis",
            "subject": "science",
            "grade_level": 8,
            "description": "The process by which plants convert light energy into chemical energy"
        },
        {
            "topic_id": "newtons_laws",
            "name": "Newton's Laws of Motion",
            "subject": "science",
            "grade_level": 9,
            "description": "The three fundamental laws that describe the relationship between motion and forces"
        },
        {
            "topic_id": "water_cycle",
            "name": "The Water Cycle",
            "subject": "science",
            "grade_level": 6,
            "description": "The continuous movement of water on, above, and below Earth's surface"
        },
        {
            "topic_id": "fractions_decimals",
            "name": "Fractions and Decimals",
            "subject": "math",
            "grade_level": 7,
            "description": "Understanding and converting between fractions and decimal numbers"
        },
        {
            "topic_id": "american_revolution",
            "name": "The American Revolution",
            "subject": "history",
            "grade_level": 8,
            "description": "The colonial revolt against British rule from 1765-1783"
        }
    ]

    created_topics = []
    for topic_data in sample_topics:
        # Check if topic already exists
        existing_topic = db.query(Topic).filter(Topic.name == topic_data["name"]).first()
        if existing_topic:
            logger.info(f"  - Topic '{topic_data['name']}' already exists, skipping")
            created_topics.append(existing_topic)
            continue

        topic = Topic(**topic_data)
        db.add(topic)
        db.commit()
        db.refresh(topic)

        created_topics.append(topic)
        logger.info(f"  ✓ Created topic: {topic.name} ({topic.subject}, Grade {topic.grade_level})")

    return created_topics


def create_sample_interests(db):
    """Create sample student interests."""
    logger.info("Creating sample interests...")

    sample_interests = [
        {"interest_id": "basketball", "name": "Basketball", "category": "sports"},
        {"interest_id": "soccer", "name": "Soccer", "category": "sports"},
        {"interest_id": "video_games", "name": "Video Games", "category": "technology"},
        {"interest_id": "cooking", "name": "Cooking", "category": "arts"},
        {"interest_id": "music", "name": "Music", "category": "arts"},
        {"interest_id": "animals", "name": "Animals", "category": "nature"},
        {"interest_id": "space", "name": "Space", "category": "science"},
        {"interest_id": "movies", "name": "Movies", "category": "entertainment"}
    ]

    created_interests = []
    for interest_data in sample_interests:
        # Check if interest already exists
        existing_interest = db.query(Interest).filter(Interest.name == interest_data["name"]).first()
        if existing_interest:
            logger.info(f"  - Interest '{interest_data['name']}' already exists, skipping")
            created_interests.append(existing_interest)
            continue

        interest = Interest(**interest_data)
        db.add(interest)
        db.commit()
        db.refresh(interest)

        created_interests.append(interest)
        logger.info(f"  ✓ Created interest: {interest.name} ({interest.category})")

    return created_interests


def main():
    """Main initialization function."""
    logger.info("=" * 60)
    logger.info("Database Initialization Script")
    logger.info("=" * 60)

    try:
        # Step 1: Initialize database tables
        init_database()

        # Step 2: Create session for data operations
        db = SessionLocal()

        try:
            # Step 3: Create test users
            users = create_test_users(db)

            # Step 4: Create sample topics
            topics = create_sample_topics(db)

            # Step 5: Create sample interests
            interests = create_sample_interests(db)

            logger.info("=" * 60)
            logger.info("✓ Database initialization completed successfully!")
            logger.info("=" * 60)
            logger.info("\nTest Accounts Created:")
            logger.info("  Student: student1@test.com (password: password123)")
            logger.info("  Teacher: teacher1@test.com (password: password123)")
            logger.info(f"\nTopics created: {len(topics)}")
            logger.info(f"Interests created: {len(interests)}")
            logger.info("\nYou can now test the content generation API!")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"✗ Error during initialization: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
