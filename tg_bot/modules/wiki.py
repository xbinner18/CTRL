import html
import re
import wikipedia
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from telegram import Chat, ParseMode, Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import run_async
from telegram.error import BadRequest
from wikipedia.exceptions import DisambiguationError, PageError


@run_async
def wiki(bot: Bot, update: Update):
    wk = re.split(pattern="wiki", string=update.effective_message.text)
    wikipedia.set_lang("en")
    if not str(wk[1]):
        update.effective_message.reply_text("Enter keywords!")
    else:
        try:
            msg = update.effective_message.reply_text("🔄 Loading...")
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(text="🔧 More Info...",
                                     url=wikipedia.page(wk).url)
            ]])
            bot.editMessageText(chat_id=update.effective_chat.id,
                                message_id=msg.message_id,
                                text=wikipedia.summary(wk, sentences=10),
                                reply_markup=keyboard)
        except PageError as e:
            update.message.reply_text(f"<code>{e}</code>", parse_mode=ParseMode.HTML)
        except BadRequest as et:
            update.message.reply_text(f"<code>{et}</code>", parse_mode=ParseMode.HTML)
        except DisambiguationError as ett:
            update.message.reply_text(
                f"Disambiguated pages found! Adjust your query accordingly.\n<i>{ett}</i>",
                parse_mode=ParseMode.HTML,
            )

__help__ = """
 - /wiki text: Returns search from wikipedia for the input text
"""
__mod_name__ = "WikiPedia"

WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
dispatcher.add_handler(WIKI_HANDLER)
