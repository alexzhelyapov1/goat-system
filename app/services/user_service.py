from sqlalchemy.orm import Session
from app.models import User, UserRole
from app.schemas import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_telegram_chat_id(db: Session, chat_id: str):
        return db.query(User).filter(User.telegram_chat_id == chat_id).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return db.query(User).get(user_id)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        hashed_password = UserService.get_password_hash(user_data.password)
        
        # The first user created is an admin
        is_first_user = db.query(User).count() == 0
        role = UserRole.ADMIN if is_first_user else UserRole.USER
        
        new_user = User(
            username=user_data.username,
            password_hash=hashed_password,
            role=role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
