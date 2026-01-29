from sqlalchemy.orm import Session
from app.models import User
from werkzeug.security import check_password_hash


class UserService:
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(User).filter_by(username=username).first()

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return check_password_hash(hashed_password, plain_password)
