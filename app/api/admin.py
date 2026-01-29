from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user, get_db
from app.models import User, UserRole
from app.schemas import UserSchema
from app.services.user_service import UserService # Assuming you have or will create a UserService for direct DB operations

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

def get_current_active_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this resource."
        )
    return current_user

@router.get("/users", response_model=List[UserSchema])
def read_users(db: Session = Depends(get_db), current_admin_user: User = Depends(get_current_active_admin_user)):
    users = db.query(User).all()
    return [UserSchema.model_validate(user) for user in users]

@router.post("/users/{user_id}/set_role", response_model=UserSchema)
def set_user_role(
    user_id: int, 
    new_role: UserRole, 
    db: Session = Depends(get_db), 
    current_admin_user: User = Depends(get_current_active_admin_user)
):
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user_to_update.id == current_admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change your own role.")

    user_to_update.role = new_role
    db.commit()
    db.refresh(user_to_update)
    return UserSchema.model_validate(user_to_update)