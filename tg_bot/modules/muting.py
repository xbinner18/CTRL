import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable

from tg_bot.modules.disable import DisableAbleCommandHandler


@run_async
@bot_admin
@user_admin
@loggable
def mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You'll need to either give me a username to mute, or reply to someone to be muted.")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not muting myself!")
        return ""

    if member := chat.get_member(int(user_id)):
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Afraid I can't stop an admin from talking!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
            message.reply_text(
                f"Muted {mention_html(member.user.id, member.user.first_name)} in <b>{html.escape(chat.title)}</b>!",
                parse_mode=ParseMode.HTML,
            )
            return f"<b>{html.escape(chat.title)}:</b>\n#MUTE\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"

        else:
            message.reply_text(
                f"This user is already muted in <b>{chat.title}</b>!",
                parse_mode=ParseMode.HTML,
            )
    else:
        message.reply_text(
            f"This user isn't in the in <b>{chat.title}</b>!",
            parse_mode=ParseMode.HTML,
        )

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def unmute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You'll need to either give me a username to unmute, or reply to someone to be unmuted.")
        return ""

    if member := chat.get_member(int(user_id)):
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("This is an admin, what do you expect me to do?")
            return ""

        elif member.status not in ['kicked', 'left', 'restricted']:
            if member.can_send_messages and member.can_send_media_messages \
                    and member.can_send_other_messages and member.can_add_web_page_previews:
                message.reply_text(
                    f"This user already has the right to speak in <b>{chat.title}</b>!",
                    parse_mode=ParseMode.HTML,
                )
                return ""
            else:
                bot.restrict_chat_member(chat.id, int(user_id),
                                         can_send_messages=True,
                                         can_send_media_messages=True,
                                         can_send_other_messages=True,
                                         can_add_web_page_previews=True)
                message.reply_text(
                    f"Unmuted {mention_html(member.user.id, member.user.first_name)} now he can speak back in <b>{html.escape(chat.title)}</b>!",
                    parse_mode=ParseMode.HTML,
                )
                return f"<b>{html.escape(chat.title)}:</b>\n#UNMUTE\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    else:
        message.reply_text("This user isn't even in the chat, unmuting them won't make them talk more than they "
                           "already do!")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user")
        return ""
    if is_user_admin(chat, user_id, member):
        message.reply_text("I really wish I could mute admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not gonna MUTE myself, are you crazy?")
        return ""

    if not reason:
        message.reply_text("You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = f"<b>{html.escape(chat.title)}:</b>\n#TEMP MUTED\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>Time:</b> {time_val}"
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=False)
            message.reply_text(
                f"Muted {mention_html(member.user.id, member.user.first_name)} for <b>{time_val}</b>!",
                parse_mode=ParseMode.HTML,
            )
            return log
        else:
            message.reply_text(
                f"This user is already muted in <b>{chat.title}<b/>!",
                parse_mode=ParseMode.HTML,
            )

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                f"Muted {mention_html(member.user.id, member.user.first_name)} for {time_val}!",
                quote=False,
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't mute that user.")

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def nomedia(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]


    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You'll need to either give me a username to restrict, or reply to someone to be restricted.")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not restricting myself!")
        return ""

    if member := chat.get_member(int(user_id)):
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Afraid I can't restrict admins!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=False,
                                     can_send_other_messages=False,
                                     can_add_web_page_previews=False)
            message.reply_text(
                f"Yep,restricted {mention_html(member.user.id, member.user.first_name)} from sending media in <b>{html.escape(chat.title)}</b>!",
                parse_mode=ParseMode.HTML,
            )
            return f"<b>{html.escape(chat.title)}:</b>\n#RESTRICTED\n<b>• Admin:</b> {mention_html(user.id, user.first_name)}\n<b>• User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>• ID:</b> <code>{user_id}</code>"
        else:
            message.reply_text(
                f"This user is already restricted in <b>{chat.title}</b>!",
                parse_mode=ParseMode.HTML,
            )
    else:
        message.reply_text(
            f"This user isn't in the <b>{chat.title}</b>!",
            parse_mode=ParseMode.HTML,
        )

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def media(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]


    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You'll need to either give me a username to unrestrict, or reply to someone to be unrestricted.")
        return ""

    member = chat.get_member(int(user_id))

    if member.status != "restricted":
        message.reply_text(
            f"This user is already have rights to send media in **{chat.title}**"
        )
        return ""

    if member.status in ['kicked', 'left', 'restricted']:
        message.reply_text("This user isn't even in the chat, unrestricting them won't make them send anything than they "
                           "already do!")

    elif member.can_send_messages and member.can_send_media_messages \
                and member.can_send_other_messages and member.can_add_web_page_previews:
        message.reply_text(
            f"This user already has the rights to send anything in <b>{chat.title}</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        bot.restrict_chat_member(chat.id, int(user_id),
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=True,
                                 can_add_web_page_previews=True)
        message.reply_text(
            f"Yep, now {mention_html(member.user.id, member.user.first_name)} can send media again in <b>{html.escape(chat.title)}</b>!",
            parse_mode=ParseMode.HTML,
        )
        user = update.effective_user  # type: Optional[User]
        return f"<b>{html.escape(chat.title)}:</b>\n#UNRESTRICTED\n<b>• Admin:</b> {mention_html(user.id, user.first_name)}\n<b>• User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>• ID:</b> <code>{user_id}</code>"
    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_nomedia(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]


    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user")
        return ""
    if is_user_admin(chat, user_id, member):
        message.reply_text("I really wish I could restrict admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not gonna RESTRICT myself, are you crazy?")
        return ""

    if not reason:
        message.reply_text("You haven't specified a time to restrict this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = f"<b>{html.escape(chat.title)}:</b>\n#TEMP RESTRICTED\n<b>• Admin:</b> {mention_html(user.id, user.first_name)}\n<b>• User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>• ID:</b> <code>{user_id}</code>\n<b>• Time:</b> {time_val}"
    if reason:
        log += f"\n<b>• Reason:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=True,
                                     can_send_media_messages=False,
                                     can_send_other_messages=False,
                                     can_add_web_page_previews=False)
            message.reply_text(
                f"Restricted {mention_html(member.user.id, member.user.first_name)} from sending media for <b>{time_val}</b>!",
                parse_mode=ParseMode.HTML,
            )
            return log
        else:
            message.reply_text(
                f"This user is already restricted in <b>{chat.title}</b>!",
                parse_mode=ParseMode.HTML,
            )

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(f"Restricted for {time_val} in {chat.title}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't restrict that user.")

    return ""


@run_async
@bot_admin
@can_restrict
def muteme(bot: Bot, update: Update, args: List[str]) -> str:
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("I wish I could... but you're an admin.")
        return

    if res := bot.restrict_chat_member(
        chat.id, user_id, can_send_messages=False
    ):
        update.effective_message.reply_text("No problem, Muted!")
        return f"<b>{html.escape(chat.title)}:</b>\n#MUTEME\n<b>User:</b> {mention_html(user.id, user.first_name)}\n<b>ID:</b> <code>{user_id}</code>"


    else:
        update.effective_message.reply_text("Huh? I can't :/")


__help__ = """
*Admin only:*
 - /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.
 - /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
 - /muteme : To muteyourself.
"""

__mod_name__ = "Muting"

MUTE_HANDLER = DisableAbleCommandHandler("mute", mute, pass_args=True, admin_ok=True)
UNMUTE_HANDLER = DisableAbleCommandHandler("unmute", unmute, pass_args=True, admin_ok=True)
TEMPMUTE_HANDLER = DisableAbleCommandHandler(["tmute", "tempmute"], temp_mute, pass_args=True, admin_ok=True)
TEMP_NOMEDIA_HANDLER = DisableAbleCommandHandler(["trestrict", "temprestrict"], temp_nomedia, pass_args=True, admin_ok=True)
NOMEDIA_HANDLER = DisableAbleCommandHandler(["restrict", "nomedia"], nomedia, pass_args=True, admin_ok=True)
MEDIA_HANDLER = DisableAbleCommandHandler("unrestrict", media, pass_args=True, admin_ok=True)
MUTEME_HANDLER = DisableAbleCommandHandler("muteme", muteme, pass_args=True, filters=Filters.group, admin_ok=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
dispatcher.add_handler(TEMP_NOMEDIA_HANDLER)
dispatcher.add_handler(NOMEDIA_HANDLER)
dispatcher.add_handler(MEDIA_HANDLER)
dispatcher.add_handler(MUTEME_HANDLER)
