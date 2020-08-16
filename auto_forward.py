import logging

from telegram import (
    Bot,
    Message,
    Update,
    ParseMode
)
from telegram.ext import (
    Updater,
    CallbackContext,
    run_async,
    Filters,
    MessageHandler
)

from utils import Config, user_format, get_filter
from utils.push import Message as Msg
from markup import main_buttons, parse_url


logger = logging.getLogger('push_helper')


@ run_async
def auto_forward(update: Update, context: CallbackContext):
    bot = Bot(token=Config.token)

    if update.message == None:
        message = update.channel_post
    else:
        message = update.message
    from_chat = update.effective_chat
    try:
        to_chat_ids = Config.forward[user_format(from_chat.username)]
    except KeyError:
        try:
            to_chat_ids = Config.forward[user_format(from_chat.id)]
        except KeyError:
            try:
                to_chat_ids = Config.forward[user_format(from_chat.username) + ":push"]
            except KeyError:
                to_chat_ids = Config.forward[str(user_format(from_chat.id)) + ":push"]
            use_push_all = True
    for to_chat_id in to_chat_ids:
        if isinstance(to_chat_id, str):
            split_result = to_chat_id.split(":")
            if split_result[1] == "push" or use_push_all:
                Msg(parse_url(message)).push(targets_additional=[split_result[0]])
        elif use_push_all:
            Msg(parse_url(message)).push(targets_additional=[to_chat_id])
        else:
            message: Message = bot.send_message(
                to_chat_id,
                text=message.text_html_urled or message.caption_html_urled,
                parse_mode=ParseMode.HTML,
                disable_notification=True,
                #reply_markup=main_buttons(message.message_id)
            )
    message.edit_reply_markup(
        reply_markup=main_buttons(message.message_id)
    )


def register(updater: Updater):
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(get_filter(Config.forward), auto_forward))


if __name__ == "__main__":
    updater = Updater(token=Config.token, use_context=True)
    register(updater)
    updater.start_polling()
    logger.info(f"Bot @{updater.bot.get_me().username} 已启动: 仅自动转发")
    updater.idle()
