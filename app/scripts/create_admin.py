import argparse
import sys
from app.core.enums import UserRole
from app.core.security import hash_password
from app.db.database import SessionLocal
import app.models  # noqa: F401
from app.models.user import User


def bootstrap_admin(email: str, password: str) -> None:
    """Create or promote a user account to the ADMIN role."""
    email = email.strip().lower()
    if "@" not in email or "." not in email:
        print("Error: Invalid email format.")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = UserRole.ADMIN.value
            user.is_active = True
            user.hashed_password = hash_password(password)
            db.commit()
            print(f"Existing user '{email}' successfully promoted to ADMIN.")
        else:
            new_admin = User(
                email=email,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(new_admin)
            db.commit()
            print(f"Admin account '{email}' created successfully.")
    except Exception as exc:
        db.rollback()
        print(f"Failed to bootstrap admin account: {exc}")
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap an administrative user account for Mizigo Marketplace.")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--password", required=True, help="Administrator password (min 8 characters)")
    args = parser.parse_args()

    bootstrap_admin(args.email, args.password)


if __name__ == "__main__":
    main()
