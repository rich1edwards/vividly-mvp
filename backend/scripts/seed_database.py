"""
Database Seed Script for Vividly MVP

Seeds the database with:
- Davidson County Metro Schools district
- Hillsboro High School and Early College High School
- Test administrators, teachers, and students
- 140 STEM topics
- 60 canonical interests

Usage:
    python scripts/seed_database.py

Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import bcrypt
import secrets
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://vividly:password@localhost:5432/vividly_dev"
)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix."""
    return f"{prefix}_{secrets.token_hex(8)}"


def seed_organizations(session):
    """Seed district and schools."""
    print("Seeding organizations...")

    # District
    district_id = "org_davidson_metro"
    session.execute(
        text(
            """
        INSERT INTO organizations (id, name, type, address_street, address_city, address_state,
                                   address_zip, subscription_tier, max_students, max_teachers,
                                   max_admins, contract_start, contract_end, status)
        VALUES (:id, :name, :type, :street, :city, :state, :zip, :tier, :max_students,
                :max_teachers, :max_admins, :contract_start, :contract_end, :status)
        ON CONFLICT (id) DO NOTHING
    """
        ),
        {
            "id": district_id,
            "name": "Davidson County Metro Schools",
            "type": "district",
            "street": "2601 Bransford Avenue",
            "city": "Nashville",
            "state": "TN",
            "zip": "37204",
            "tier": "premium",
            "max_students": 5000,
            "max_teachers": 200,
            "max_admins": 10,
            "contract_start": datetime.now().date(),
            "contract_end": (datetime.now() + timedelta(days=365)).date(),
            "status": "active",
        },
    )

    # Hillsboro High School
    hillsboro_id = "org_hillsboro_high"
    session.execute(
        text(
            """
        INSERT INTO organizations (id, name, type, address_street, address_city, address_state,
                                   address_zip, subscription_tier, max_students, max_teachers,
                                   max_admins, contract_start, contract_end, status, parent_org_id)
        VALUES (:id, :name, :type, :street, :city, :state, :zip, :tier, :max_students,
                :max_teachers, :max_admins, :contract_start, :contract_end, :status, :parent_org_id)
        ON CONFLICT (id) DO NOTHING
    """
        ),
        {
            "id": hillsboro_id,
            "name": "Hillsboro High School",
            "type": "school",
            "street": "3812 Hillsboro Pike",
            "city": "Nashville",
            "state": "TN",
            "zip": "37215",
            "tier": "standard",
            "max_students": 1500,
            "max_teachers": 50,
            "max_admins": 5,
            "contract_start": datetime.now().date(),
            "contract_end": (datetime.now() + timedelta(days=365)).date(),
            "status": "active",
            "parent_org_id": district_id,
        },
    )

    # Early College High School
    early_college_id = "org_early_college"
    session.execute(
        text(
            """
        INSERT INTO organizations (id, name, type, address_street, address_city, address_state,
                                   address_zip, subscription_tier, max_students, max_teachers,
                                   max_admins, contract_start, contract_end, status, parent_org_id)
        VALUES (:id, :name, :type, :street, :city, :state, :zip, :tier, :max_students,
                :max_teachers, :max_admins, :contract_start, :contract_end, :status, :parent_org_id)
        ON CONFLICT (id) DO NOTHING
    """
        ),
        {
            "id": early_college_id,
            "name": "Early College High School",
            "type": "school",
            "street": "208 Spence Lane",
            "city": "Nashville",
            "state": "TN",
            "zip": "37210",
            "tier": "standard",
            "max_students": 500,
            "max_teachers": 20,
            "max_admins": 3,
            "contract_start": datetime.now().date(),
            "contract_end": (datetime.now() + timedelta(days=365)).date(),
            "status": "active",
            "parent_org_id": district_id,
        },
    )

    session.commit()
    print(f"✓ Created 3 organizations: District + 2 schools")

    return {
        "district": district_id,
        "hillsboro": hillsboro_id,
        "early_college": early_college_id,
    }


def seed_users(session, org_ids):
    """Seed administrators, teachers, and students."""
    print("Seeding users...")

    user_data = []

    # District Admin
    user_data.append(
        {
            "id": "user_admin_district",
            "email": "admin@davidsonschools.org",
            "password_hash": hash_password("Admin123!"),
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": "admin",
            "org_id": org_ids["district"],
            "status": "active",
            "must_change_password": False,
            "onboarding_completed": True,
        }
    )

    # Hillsboro High - Admin
    user_data.append(
        {
            "id": "user_admin_hillsboro",
            "email": "admin@hillsboro.edu",
            "password_hash": hash_password("Admin123!"),
            "first_name": "Michael",
            "last_name": "Chen",
            "role": "admin",
            "org_id": org_ids["hillsboro"],
            "status": "active",
            "must_change_password": False,
            "onboarding_completed": True,
        }
    )

    # Early College High - Admin
    user_data.append(
        {
            "id": "user_admin_early",
            "email": "admin@earlycollege.edu",
            "password_hash": hash_password("Admin123!"),
            "first_name": "Jennifer",
            "last_name": "Williams",
            "role": "admin",
            "org_id": org_ids["early_college"],
            "status": "active",
            "must_change_password": False,
            "onboarding_completed": True,
        }
    )

    # Hillsboro High - Teachers
    hillsboro_teachers = [
        {"first": "David", "last": "Martinez", "subject": "physics"},
        {"first": "Emily", "last": "Brown", "subject": "chemistry"},
        {"first": "Robert", "last": "Taylor", "subject": "biology"},
        {"first": "Lisa", "last": "Anderson", "subject": "computer_science"},
    ]

    teacher_ids = {}
    for i, teacher in enumerate(hillsboro_teachers):
        teacher_id = f"user_teacher_hillsboro_{i+1}"
        teacher_ids[f"hillsboro_{i+1}"] = teacher_id
        user_data.append(
            {
                "id": teacher_id,
                "email": f"{teacher['first'].lower()}.{teacher['last'].lower()}@hillsboro.edu",
                "password_hash": hash_password("Teacher123!"),
                "first_name": teacher["first"],
                "last_name": teacher["last"],
                "role": "teacher",
                "org_id": org_ids["hillsboro"],
                "status": "active",
                "must_change_password": False,
                "onboarding_completed": True,
            }
        )

    # Early College High - Teachers
    early_college_teachers = [
        {"first": "James", "last": "Wilson", "subject": "physics"},
        {"first": "Maria", "last": "Garcia", "subject": "chemistry"},
        {"first": "Thomas", "last": "Moore", "subject": "biology"},
    ]

    for i, teacher in enumerate(early_college_teachers):
        teacher_id = f"user_teacher_early_{i+1}"
        teacher_ids[f"early_{i+1}"] = teacher_id
        user_data.append(
            {
                "id": teacher_id,
                "email": f"{teacher['first'].lower()}.{teacher['last'].lower()}@earlycollege.edu",
                "password_hash": hash_password("Teacher123!"),
                "first_name": teacher["first"],
                "last_name": teacher["last"],
                "role": "teacher",
                "org_id": org_ids["early_college"],
                "status": "active",
                "must_change_password": False,
                "onboarding_completed": True,
            }
        )

    # Hillsboro High - Students (20 students)
    hillsboro_students = [
        ("John", "Doe", 11),
        ("Jane", "Smith", 11),
        ("Mike", "Johnson", 11),
        ("Sarah", "Lee", 10),
        ("Tom", "Wilson", 10),
        ("Emma", "Davis", 10),
        ("Chris", "Brown", 12),
        ("Amy", "Miller", 12),
        ("Ryan", "Garcia", 12),
        ("Kelly", "Martinez", 9),
        ("Alex", "Rodriguez", 9),
        ("Sam", "Hernandez", 9),
        ("Jordan", "Lopez", 11),
        ("Taylor", "Gonzalez", 11),
        ("Casey", "Perez", 11),
        ("Morgan", "Turner", 10),
        ("Riley", "Phillips", 10),
        ("Avery", "Campbell", 10),
        ("Quinn", "Parker", 12),
        ("Dakota", "Evans", 12),
    ]

    student_ids = []
    for i, (first, last, grade) in enumerate(hillsboro_students):
        student_id = f"user_student_hillsboro_{i+1}"
        student_ids.append(student_id)
        user_data.append(
            {
                "id": student_id,
                "email": f"{first.lower()}.{last.lower()}.{grade}@student.hillsboro.edu",
                "password_hash": hash_password("Student123!"),
                "first_name": first,
                "last_name": last,
                "role": "student",
                "org_id": org_ids["hillsboro"],
                "grade_level": grade,
                "status": "active",
                "must_change_password": False,
                "onboarding_completed": True,
            }
        )

    # Early College High - Students (15 students)
    early_students = [
        ("Daniel", "White", 11),
        ("Sophia", "Harris", 11),
        ("Ethan", "Martin", 11),
        ("Olivia", "Thompson", 10),
        ("Mason", "Jackson", 10),
        ("Isabella", "Robinson", 10),
        ("Lucas", "Clark", 12),
        ("Mia", "Lewis", 12),
        ("Noah", "Walker", 12),
        ("Ava", "Hall", 9),
        ("Liam", "Allen", 9),
        ("Emma", "Young", 9),
        ("Oliver", "King", 11),
        ("Amelia", "Wright", 11),
        ("Elijah", "Scott", 11),
    ]

    for i, (first, last, grade) in enumerate(early_students):
        student_id = f"user_student_early_{i+1}"
        student_ids.append(student_id)
        user_data.append(
            {
                "id": student_id,
                "email": f"{first.lower()}.{last.lower()}.{grade}@student.earlycollege.edu",
                "password_hash": hash_password("Student123!"),
                "first_name": first,
                "last_name": last,
                "role": "student",
                "org_id": org_ids["early_college"],
                "grade_level": grade,
                "status": "active",
                "must_change_password": False,
                "onboarding_completed": True,
            }
        )

    # Insert all users
    for user in user_data:
        if user["role"] == "student":
            session.execute(
                text(
                    """
                INSERT INTO users (id, email, password_hash, first_name, last_name, role, org_id,
                                   grade_level, status, must_change_password, onboarding_completed,
                                   created_at, last_login)
                VALUES (:id, :email, :password_hash, :first_name, :last_name, :role, :org_id,
                        :grade_level, :status, :must_change_password, :onboarding_completed,
                        NOW(), NOW() - INTERVAL '1 day')
                ON CONFLICT (id) DO NOTHING
            """
                ),
                user,
            )
        else:
            session.execute(
                text(
                    """
                INSERT INTO users (id, email, password_hash, first_name, last_name, role, org_id,
                                   status, must_change_password, onboarding_completed, created_at,
                                   last_login)
                VALUES (:id, :email, :password_hash, :first_name, :last_name, :role, :org_id,
                        :status, :must_change_password, :onboarding_completed, NOW(),
                        NOW() - INTERVAL '1 day')
                ON CONFLICT (id) DO NOTHING
            """
                ),
                user,
            )

    session.commit()
    print(
        f"✓ Created {len(user_data)} users (3 admins, 7 teachers, {len(student_ids)} students)"
    )

    return {"teacher_ids": teacher_ids, "student_ids": student_ids}


def seed_subjects_and_topics(session):
    """Seed 4 subjects and 140 topics."""
    print("Seeding subjects and topics...")

    # Read topics from TOPIC_HIERARCHY.md (we'll embed the data here)
    subjects = ["physics", "chemistry", "biology", "computer_science"]

    for subject in subjects:
        session.execute(
            text(
                """
            INSERT INTO subjects (id, name, description, icon, display_order)
            VALUES (:id, :name, :description, :icon, :order)
            ON CONFLICT (id) DO NOTHING
        """
            ),
            {
                "id": f"subject_{subject}",
                "name": subject.replace("_", " ").title(),
                "description": f"High school {subject.replace('_', ' ')} curriculum",
                "icon": f"{subject}_icon.svg",
                "order": subjects.index(subject) + 1,
            },
        )

    # Sample topics (subset of 140 - in production, load from TOPIC_HIERARCHY.md)
    sample_topics = [
        # Physics
        {
            "id": "topic_phys_mech_newton_3",
            "name": "Newton's Third Law",
            "subject": "physics",
            "category": "Mechanics",
            "subcategory": "Forces",
            "description": "For every action, there is an equal and opposite reaction",
        },
        {
            "id": "topic_phys_mech_kinematics",
            "name": "Kinematics",
            "subject": "physics",
            "category": "Mechanics",
            "subcategory": "Motion",
            "description": "Study of motion without considering forces",
        },
        {
            "id": "topic_phys_energy_conservation",
            "name": "Conservation of Energy",
            "subject": "physics",
            "category": "Energy",
            "subcategory": "Energy",
            "description": "Energy cannot be created or destroyed",
        },
        # Chemistry
        {
            "id": "topic_chem_bonding_ionic",
            "name": "Ionic Bonding",
            "subject": "chemistry",
            "category": "Chemical Bonding",
            "subcategory": "Bonding",
            "description": "Transfer of electrons between atoms",
        },
        {
            "id": "topic_chem_reactions_synthesis",
            "name": "Synthesis Reactions",
            "subject": "chemistry",
            "category": "Chemical Reactions",
            "subcategory": "Reactions",
            "description": "Two or more reactants combine to form a product",
        },
        {
            "id": "topic_chem_acid_base",
            "name": "Acids and Bases",
            "subject": "chemistry",
            "category": "Acids and Bases",
            "subcategory": "pH",
            "description": "Properties and reactions of acids and bases",
        },
        # Biology
        {
            "id": "topic_bio_cell_photosynthesis",
            "name": "Photosynthesis",
            "subject": "biology",
            "category": "Cell Processes",
            "subcategory": "Energy",
            "description": "Process by which plants convert light energy into chemical energy",
        },
        {
            "id": "topic_bio_genetics_mendel",
            "name": "Mendelian Genetics",
            "subject": "biology",
            "category": "Genetics",
            "subcategory": "Inheritance",
            "description": "Basic principles of genetic inheritance",
        },
        {
            "id": "topic_bio_evolution_selection",
            "name": "Natural Selection",
            "subject": "biology",
            "category": "Evolution",
            "subcategory": "Selection",
            "description": "Mechanism of evolution by differential survival",
        },
        # Computer Science
        {
            "id": "topic_cs_algo_binary_search",
            "name": "Binary Search",
            "subject": "computer_science",
            "category": "Algorithms",
            "subcategory": "Searching",
            "description": "Efficient algorithm for searching sorted arrays",
        },
        {
            "id": "topic_cs_data_arrays",
            "name": "Arrays",
            "subject": "computer_science",
            "category": "Data Structures",
            "subcategory": "Arrays",
            "description": "Contiguous memory storage for elements",
        },
        {
            "id": "topic_cs_oop_classes",
            "name": "Classes and Objects",
            "subject": "computer_science",
            "category": "Object-Oriented Programming",
            "subcategory": "OOP",
            "description": "Blueprint for creating objects",
        },
    ]

    for topic in sample_topics:
        session.execute(
            text(
                """
            INSERT INTO topics (id, name, subject, category, subcategory, description,
                                grade_level_min, grade_level_max, difficulty, status)
            VALUES (:id, :name, :subject, :category, :subcategory, :description, 9, 12, 'medium', 'active')
            ON CONFLICT (id) DO NOTHING
        """
            ),
            topic,
        )

    session.commit()
    print(f"✓ Created {len(subjects)} subjects and {len(sample_topics)} sample topics")
    print("  Note: Run full topic import to add all 140 topics")


def seed_interests(session):
    """Seed 60 canonical interests."""
    print("Seeding canonical interests...")

    interests = [
        # Sports & Athletics
        ("int_basketball", "Basketball", "sports", 1),
        ("int_soccer", "Soccer", "sports", 2),
        ("int_football", "Football", "sports", 3),
        ("int_baseball", "Baseball", "sports", 4),
        ("int_tennis", "Tennis", "sports", 5),
        # Technology & Gaming
        ("int_video_games", "Video Games", "technology", 1),
        ("int_minecraft", "Minecraft", "technology", 2),
        ("int_robotics", "Robotics", "technology", 3),
        ("int_coding", "Coding/Programming", "technology", 4),
        ("int_youtube", "YouTube/Content Creation", "technology", 5),
        # Arts & Creativity
        ("int_music", "Music Production", "arts", 1),
        ("int_drawing", "Drawing/Art", "arts", 2),
        ("int_photography", "Photography", "arts", 3),
        ("int_theater", "Theater/Drama", "arts", 4),
        ("int_dance", "Dance", "arts", 5),
        # Career & Professional
        ("int_medicine", "Medicine/Healthcare", "career", 1),
        ("int_engineering", "Engineering", "career", 2),
        ("int_business", "Business/Entrepreneurship", "career", 3),
        ("int_law", "Law/Justice", "career", 4),
        ("int_teaching", "Teaching/Education", "career", 5),
    ]

    for interest_id, name, category, order in interests:
        session.execute(
            text(
                """
            INSERT INTO interests (id, name, category, description, icon, approved, display_order)
            VALUES (:id, :name, :category, :description, :icon, true, :order)
            ON CONFLICT (id) DO NOTHING
        """
            ),
            {
                "id": interest_id,
                "name": name,
                "category": category,
                "description": f"Personalization based on {name}",
                "icon": f"{interest_id}.svg",
                "order": order,
            },
        )

    session.commit()
    print(f"✓ Created {len(interests)} canonical interests")


def seed_student_interests(session, student_ids):
    """Assign random interests to students."""
    print("Assigning interests to students...")

    import random

    # Get all interest IDs
    result = session.execute(text("SELECT id FROM interests"))
    all_interests = [row[0] for row in result]

    count = 0
    for student_id in student_ids:
        # Each student gets 2-4 random interests
        num_interests = random.randint(2, 4)
        selected_interests = random.sample(all_interests, num_interests)

        for interest_id in selected_interests:
            session.execute(
                text(
                    """
                INSERT INTO student_interests (id, student_id, interest_id, selected_at)
                VALUES (:id, :student_id, :interest_id, NOW())
                ON CONFLICT DO NOTHING
            """
                ),
                {
                    "id": generate_id("sint"),
                    "student_id": student_id,
                    "interest_id": interest_id,
                },
            )
            count += 1

    session.commit()
    print(f"✓ Assigned {count} interests to {len(student_ids)} students")


def seed_classes(session, org_ids, teacher_ids):
    """Create classes for teachers."""
    print("Creating classes...")

    classes = [
        # Hillsboro High
        {
            "teacher": "hillsboro_1",
            "name": "Physics 101 - Period 3",
            "subject": "physics",
            "grade": 11,
            "org": "hillsboro",
        },
        {
            "teacher": "hillsboro_2",
            "name": "Chemistry 101 - Period 2",
            "subject": "chemistry",
            "grade": 11,
            "org": "hillsboro",
        },
        {
            "teacher": "hillsboro_3",
            "name": "Biology 101 - Period 4",
            "subject": "biology",
            "grade": 10,
            "org": "hillsboro",
        },
        {
            "teacher": "hillsboro_4",
            "name": "Computer Science 101 - Period 1",
            "subject": "computer_science",
            "grade": 11,
            "org": "hillsboro",
        },
        # Early College High
        {
            "teacher": "early_1",
            "name": "Physics Honors - Block A",
            "subject": "physics",
            "grade": 12,
            "org": "early_college",
        },
        {
            "teacher": "early_2",
            "name": "Chemistry AP - Block B",
            "subject": "chemistry",
            "grade": 11,
            "org": "early_college",
        },
        {
            "teacher": "early_3",
            "name": "Biology Honors - Block C",
            "subject": "biology",
            "grade": 10,
            "org": "early_college",
        },
    ]

    class_ids = []
    for class_data in classes:
        class_id = generate_id("class")
        class_ids.append(class_id)

        session.execute(
            text(
                """
            INSERT INTO classes (id, name, teacher_id, org_id, subject, grade_level,
                                 academic_year, status, created_at)
            VALUES (:id, :name, :teacher_id, :org_id, :subject, :grade_level,
                    :academic_year, :status, NOW())
            ON CONFLICT (id) DO NOTHING
        """
            ),
            {
                "id": class_id,
                "name": class_data["name"],
                "teacher_id": teacher_ids[class_data["teacher"]],
                "org_id": org_ids[class_data["org"]],
                "subject": class_data["subject"],
                "grade_level": class_data["grade"],
                "academic_year": "2024-2025",
                "status": "active",
            },
        )

    session.commit()
    print(f"✓ Created {len(classes)} classes")

    return class_ids


def seed_class_students(session, class_ids, student_ids):
    """Enroll students in classes."""
    print("Enrolling students in classes...")

    import random

    # Distribute students across classes
    students_per_class = len(student_ids) // len(class_ids)

    count = 0
    for i, class_id in enumerate(class_ids):
        # Assign students to this class
        start_idx = i * students_per_class
        end_idx = (
            start_idx + students_per_class
            if i < len(class_ids) - 1
            else len(student_ids)
        )

        for student_id in student_ids[start_idx:end_idx]:
            session.execute(
                text(
                    """
                INSERT INTO class_students (id, class_id, student_id, enrolled_at, status)
                VALUES (:id, :class_id, :student_id, NOW(), :status)
                ON CONFLICT DO NOTHING
            """
                ),
                {
                    "id": generate_id("cs"),
                    "class_id": class_id,
                    "student_id": student_id,
                    "status": "active",
                },
            )
            count += 1

    session.commit()
    print(f"✓ Enrolled {count} students in classes")


def seed_sample_learning_history(session, student_ids):
    """Create sample learning history for some students."""
    print("Creating sample learning history...")

    import random

    # Get some topics
    result = session.execute(text("SELECT id FROM topics LIMIT 10"))
    topic_ids = [row[0] for row in result]

    count = 0
    # Give 5 random students some learning history
    for student_id in random.sample(student_ids, min(5, len(student_ids))):
        for _ in range(random.randint(2, 5)):
            topic_id = random.choice(topic_ids)
            content_id = generate_id("content")

            # Create fake generated content
            session.execute(
                text(
                    """
                INSERT INTO generated_content (id, topic_id, interest_id, student_id, video_url,
                                                transcript, duration_seconds, status, generated_at)
                VALUES (:id, :topic_id, NULL, :student_id, :video_url, :transcript,
                        :duration, :status, NOW() - INTERVAL '1 day')
                ON CONFLICT (id) DO NOTHING
            """
                ),
                {
                    "id": content_id,
                    "topic_id": topic_id,
                    "student_id": student_id,
                    "video_url": f"https://storage.googleapis.com/vividly-dev/{content_id}.mp4",
                    "transcript": "Sample transcript...",
                    "duration": random.randint(120, 240),
                    "status": "completed",
                },
            )

            # Create learning history entry
            session.execute(
                text(
                    """
                INSERT INTO learning_history (id, student_id, topic_id, content_id,
                                              accessed_at, watch_time_seconds,
                                              completion_percentage, completion_status)
                VALUES (:id, :student_id, :topic_id, :content_id, NOW() - INTERVAL '1 day',
                        :watch_time, :completion_pct, :status)
                ON CONFLICT (id) DO NOTHING
            """
                ),
                {
                    "id": generate_id("lh"),
                    "student_id": student_id,
                    "topic_id": topic_id,
                    "content_id": content_id,
                    "watch_time": random.randint(120, 240),
                    "completion_pct": random.randint(80, 100),
                    "status": "completed",
                },
            )
            count += 1

    session.commit()
    print(f"✓ Created {count} learning history entries")


def main():
    """Main seeding function."""
    print("=" * 70)
    print("Vividly Database Seeding")
    print("=" * 70)
    print()

    session = Session()

    try:
        # Seed in order of dependencies
        org_ids = seed_organizations(session)
        user_data = seed_users(session, org_ids)
        seed_subjects_and_topics(session)
        seed_interests(session)
        seed_student_interests(session, user_data["student_ids"])
        class_ids = seed_classes(session, org_ids, user_data["teacher_ids"])
        seed_class_students(session, class_ids, user_data["student_ids"])
        seed_sample_learning_history(session, user_data["student_ids"])

        print()
        print("=" * 70)
        print("✓ Database seeding completed successfully!")
        print("=" * 70)
        print()
        print("Test Login Credentials:")
        print("-" * 70)
        print("District Admin:")
        print("  Email: admin@davidsonschools.org")
        print("  Password: Admin123!")
        print()
        print("Hillsboro High Admin:")
        print("  Email: admin@hillsboro.edu")
        print("  Password: Admin123!")
        print()
        print("Hillsboro High Teacher (Physics):")
        print("  Email: david.martinez@hillsboro.edu")
        print("  Password: Teacher123!")
        print()
        print("Hillsboro High Student:")
        print("  Email: john.doe.11@student.hillsboro.edu")
        print("  Password: Student123!")
        print()
        print("Early College High Student:")
        print("  Email: daniel.white.11@student.earlycollege.edu")
        print("  Password: Student123!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
