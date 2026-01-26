import logging
from app import create_app
from app.telegram_bot import (
    start,
    task_list,
    task_delete,
    task_delete_confirm,

    add_task_start,
    get_title,
    get_notify_choice,
    get_notify_at,
    CONFIRM_DELETE,
    GET_TITLE,
    GET_NOTIFY_CHOICE,
    GET_NOTIFY_AT
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = create_app()

def main():
    with app.app_context():

        token = app.config["TELEGRAM_BOT_TOKEN"]
        if not token:
            logger.warning("Telegram bot token not configured. Bot will not run.")
            return

        application = ApplicationBuilder().token(token).build()

        from app.telegram_utils import send_telegram_message
        from app.models import User
        import traceback
        import asyncio

        async def error_handler(update, context):
            """Log the error and send a message to 'alex'."""
            logger.exception("Exception while handling an update:")

            error_message = f"🚨 *Bot Error* 🚨\n\n" \
                            f"**Error Type:** `{type(context.error).__name__}`\n" \
                            f"**Message:** `{str(context.error)}`\n"

            if update and update.effective_user:
                error_message += f"**User:** @{update.effective_user.username} (ID: {update.effective_user.id})\n"
            if update and update.effective_chat:
                error_message += f"**Chat ID:** `{update.effective_chat.id}`\n"
            if update and update.message and update.message.text:
                error_message += f"**Message Text:** `{update.message.text}`\n"

            error_message += f"**Traceback:**\n```\n{traceback.format_exc()}\n```"

            # Try to send message to 'alex'
            with app.app_context():
                alex_user = User.query.filter_by(username='alex').first()
                if alex_user and alex_user.telegram_chat_id:
                    try:
                        # Directly await the async send_telegram_message
                        await send_telegram_message(
                            chat_id=alex_user.telegram_chat_id,
                            message=error_message,
                            app_instance=app
                        )
                    except Exception as tg_e:
                        logger.error(f"Failed to send Telegram error report from bot error handler: {tg_e}", exc_info=True)
                else:
                    logger.warning("Could not find user 'alex' or their Telegram chat ID for bot error reporting.")

            # Optionally, inform the user who caused the error
            if update and update.effective_message:
                await update.effective_message.reply_text("An unexpected error occurred while processing your request. The issue has been reported.")
        
        application.add_error_handler(error_handler)

        application.add_handler(CommandHandler("start", start))
        task_list_commands = [
            "task_list_all", "task_list_current", "task_list_inbox",
            "task_list_someday", "task_list_rest", "task_list_routine",
        ]
        application.add_handler(CommandHandler(task_list_commands, task_list))

        delete_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("task_delete", task_delete)],
            states={CONFIRM_DELETE: [CallbackQueryHandler(task_delete_confirm)]},
            fallbacks=[],
        )
        application.add_handler(delete_conv_handler)

        add_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler(
                    ["add_current", "add_inbox", "add_someday", "add_rest", "add_routine"],
                    add_task_start,
                )
            ],
            states={
                GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
                GET_NOTIFY_CHOICE: [CallbackQueryHandler(get_notify_choice)],
                GET_NOTIFY_AT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notify_at)],
            },
            fallbacks=[],
        )
        application.add_handler(add_conv_handler)


        logger.info("Starting Telegram bot polling...")
        application.run_polling()

if __name__ == "__main__":
    main()
