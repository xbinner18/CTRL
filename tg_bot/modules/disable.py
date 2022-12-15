from typing import Union, List, Optional

from future.utils import string_types
from telegram import ParseMode, Update, Bot, Chat, User
from telegram.ext import CommandHandler, RegexHandler, Filters
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.handlers import CMD_STARTERS
from tg_bot.modules.helper_funcs.misc import is_module_loaded
from tg_bot.modules.helper_funcs.alternate import send_message
from tg_bot.modules.connection import connected

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
    from telegram.ext.dispatcher import run_async

    from tg_bot.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):
        def __init__(self, command, callback, admin_ok=False, **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            chat = update.effective_chat  # type: Optional[Chat]
            user = update.effective_user  # type: Optional[User]
            if super().check_update(update):
                # Should be safe since check_update passed.
                command = update.effective_message.text_html.split(None, 1)[0][1:].split('@')[0]

                # disabled, admincmd, user admin
                if sql.is_command_disabled(chat.id, command):
                    return command in ADMIN_CMDS and is_user_admin(chat, user.id)

                # not disabled
                else:
                    return True

            return False


    class DisableAbleRegexHandler(RegexHandler):
        def __init__(self, pattern, callback, friendly="", **kwargs):
            super().__init__(pattern, callback, **kwargs)
            DISABLE_OTHER.append(friendly or pattern)
            self.friendly = friendly or pattern

        def check_update(self, update):
            chat = update.effective_chat
            return super().check_update(update) and not sql.is_command_disabled(chat.id, self.friendly)


    @run_async
    @user_admin
    def disable(bot: Bot, update: Update, args: List[str]):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user

        conn = connected(bot, update, chat, user.id, need_admin=True)
        if conn:
            chat = dispatcher.bot.getChat(conn)
            chat_name = dispatcher.bot.getChat(conn).title
        else:
            if update.effective_message.chat.type == "private":
                send_message(
                    update.effective_message,
                    "This command meant to be used in group not in PM",
                )
                return ""
            chat = update.effective_chat
            chat_name = update.effective_message.chat.title

        if args:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, disable_cmd)
                if conn:
                    text = f"Disabled the use of `{disable_cmd}` command in *{chat_name}*!"
                else:
                    text = f"Disabled the use of `{disable_cmd}` command!"
                send_message(
                    update.effective_message, text, parse_mode=ParseMode.MARKDOWN
                )
            else:
                send_message(update.effective_message, "This command can't be disabled")

        else:
            send_message(update.effective_message, "What should I disable?")


    @run_async
    @user_admin
    def enable(bot: Bot, update: Update, args: List[str]):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user

        conn = connected(bot, update, chat, user.id, need_admin=True)
        if conn:
            chat = dispatcher.bot.getChat(conn)
            chat_id = conn
            chat_name = dispatcher.bot.getChat(conn).title
        else:
            if update.effective_message.chat.type == "private":
                send_message(
                    update.effective_message,
                    "This command is meant to be used in group not in PM",
                )
                return ""
            chat = update.effective_chat
            chat_id = update.effective_chat.id
            chat_name = update.effective_message.chat.title

        if args:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                if conn:
                    text = f"Enabled the use of `{enable_cmd}` command in *{chat_name}*!"
                else:
                    text = f"Enabled the use of `{enable_cmd}` command!"
                send_message(
                    update.effective_message, text, parse_mode=ParseMode.MARKDOWN
                )
            else:
                send_message(update.effective_message, "Is that even disabled?")

        else:
            send_message(update.effective_message, "What should I enable?")


    @run_async
    @user_admin
    def list_cmds(bot: Bot, update: Update):
        if DISABLE_CMDS + DISABLE_OTHER:
            result = "".join(
                f" - `{escape_markdown(cmd)}`\n"
                for cmd in set(DISABLE_CMDS + DISABLE_OTHER)
            )
            update.effective_message.reply_text(
                f"The following commands are toggleable:\n{result}",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            update.effective_message.reply_text("No commands can be disabled.")


    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "No commands are disabled!"

        result = "".join(f" - `{escape_markdown(cmd)}`\n" for cmd in disabled)
        return f"The following commands are currently restricted:\n{result}"


    @run_async
    def commands(bot: Bot, update: Update):
        chat = update.effective_chat
        user = update.effective_user
        if conn := connected(bot, update, chat, user.id, need_admin=True):
            chat = dispatcher.bot.getChat(conn)
            chat_id = conn
        else:
            if update.effective_message.chat.type == "private":
                send_message(
                    update.effective_message,
                    "This command is meant to use in group not in PM",
                )
                return ""
            chat = update.effective_chat
            chat_id = update.effective_chat.id

        text = build_curr_disabled(chat.id)
        send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)


    def __stats__():
        return f"{sql.num_disabled()} disabled items, across {sql.num_chats()} chats."


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        return build_curr_disabled(chat_id)


    __mod_name__ = "Command disabling"

    __help__ = """
 - /cmds: check the current status of disabled commands

*Admin only:*
 - /enable <cmd name>: enable that command
 - /disable <cmd name>: disable that command
 - /listcmds: list all possible toggleable commands
    """

    DISABLE_HANDLER = CommandHandler("disable", disable, pass_args=True) #, filters=Filters.group)
    ENABLE_HANDLER = CommandHandler("enable", enable, pass_args=True) #, filters=Filters.group)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands) #, filters=Filters.group)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds, filters=Filters.group)

    dispatcher.add_handler(DISABLE_HANDLER)
    dispatcher.add_handler(ENABLE_HANDLER)
    dispatcher.add_handler(COMMANDS_HANDLER)
    dispatcher.add_handler(TOGGLE_HANDLER)

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleRegexHandler = RegexHandler
