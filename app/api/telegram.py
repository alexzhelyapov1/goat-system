from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import UserTelegramUpdate, UserSchema, UserTelegramSendMessage
from app.queue import redis_conn
from app.telegram_utils import send_telegram_message
from config import Config
import asyncio

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
)

@router.post("/connect", response_model=UserSchema)
def connect_telegram(
    token: str, 
    chat_id: str, 
    username: str, 
    db: Session = Depends(get_db)
):
    user_id = redis_conn.get(f"telegram_token:{token}")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    user.telegram_chat_id = chat_id
    user.telegram_username = username
    db.commit()
    db.refresh(user)
    redis_conn.delete(f"telegram_token:{token}") # Invalidate token after use
    return UserSchema.model_validate(user)


@router.post("/disconnect", response_model=UserSchema)
def disconnect_telegram(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.telegram_chat_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram not connected.")
    
    current_user.telegram_chat_id = None
    current_user.telegram_username = None
    db.commit()
    db.refresh(current_user)
    return UserSchema.model_validate(current_user)

@router.post("/send_error_report")
async def send_error_report(
    message_data: UserTelegramSendMessage, 
    # This endpoint does not require authentication as it's for error reporting from the frontend.
    # It sends to a specific chat_id, not necessarily the current_user's chat_id.
    # current_user: User = Depends(get_current_user) # If we wanted to secure it.
):
    telegram_bot_token = Config.TELEGRAM_BOT_TOKEN
    if not telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Telegram bot token not configured.")
    
    try:
        await send_telegram_message(
            chat_id=message_data.chat_id, 
            message=message_data.message, 
            # app_instance=None as it's outside Flask app context now
        )
        return {"status": "success", "message": "Error report sent to Telegram."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send Telegram message: {e}")
