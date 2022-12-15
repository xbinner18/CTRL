import html
import locale
import json
import requests
import random, re
from datetime import datetime
from typing import Optional, List
from tg_bot.modules.translations.strings import tld
from io import BytesIO
from requests import get
from random import randint
from telegram import Message, Chat, Update, Bot, MessageEntity, ParseMode
from tg_bot.modules.helper_funcs.alternate import send_message


from telegram.error import BadRequest
from telegram import ParseMode, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, MAPS_API

from tg_bot.__main__ import STATS, USER_INFO, TOKEN
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters



RUN_STRINGS = (
    "Where do you think you're going?",
    "Huh? what? did they get away?",
    "ZZzzZZzz... Huh? what? oh, just them again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear that's fun.",
    "Go bother someone else, no-one here cares.",
    "You can run, but you can't hide.",
    "Is that all you've got?",
    "I'm behind you...",
    "You've got company!",
    "We can do this the easy way, or the hard way.",
    "You just don't get it, do you?",
    "Yeah, you better run!",
    "Please, remind me how much I care?",
    "I'd run faster if I were you.",
    "That's definitely the droid we're looking for.",
    "May the odds be ever in your favour.",
    "Famous last words.",
    "And they disappeared forever, never to be seen again.",
    "\"Oh, look at me! I'm so cool, I can run from a bot!\" - this person",
    "Yeah yeah, just tap /kickme already.",
    "Here, take this ring and head to Mordor while you're at it.",
    "Legend has it, they're still running...",
    "Unlike Harry Potter, your parents can't protect you from me.",
    "Fear leads to anger. Anger leads to hate. Hate leads to suffering. If you keep running in fear, you might "
    "be the next Vader.",
    "Multiple calculations later, I have decided my interest in your shenanigans is exactly 0.",
    "Legend has it, they're still running.",
    "Keep it up, not sure we want you here anyway.",
    "You're a wiza- Oh. Wait. You're not Harry, keep moving.",
    "NO RUNNING IN THE HALLWAYS!",
    "Hasta la vista, baby.",
    "Who let the dogs out?",
    "It's funny, because no one cares.",
    "Ah, what a waste. I liked that one.",
    "Frankly, my dear, I don't give a damn.",
    "My milkshake brings all the boys to yard... So run faster!",
    "You can't HANDLE the truth!",
    "A long time ago, in a galaxy far far away... Someone would've cared about that. Not anymore though.",
    "Hey, look at them! They're running from the inevitable banhammer... Cute.",
    "Han shot first. So will I.",
    "What are you running after, a white rabbit?",
    "As The Doctor would say... RUN!",
)

SLAP_TEMPLATES = (
    "{user1} {hits} {user2} with a {item}.",
    "{user1} {hits} {user2} in the face with a {item}.",
    "{user1} {hits} {user2} around a bit with a {item}.",
    "{user1} {throws} a {item} at {user2}.",
    "{user1} grabs a {item} and {throws} it at {user2}'s face.",
    "{user1} launches a {item} in {user2}'s general direction.",
    "{user1} starts slapping {user2} silly with a {item}.",
    "{user1} pins {user2} down and repeatedly {hits} them with a {item}.",
    "{user1} grabs up a {item} and {hits} {user2} with it.",
    "{user1} ties {user2} to a chair and {throws} a {item} at them.",
    "{user1} gave a friendly push to help {user2} learn to swim in lava."
)

ITEMS = (
    "cast iron skillet",
    "large trout",
    "baseball bat",
    "cricket bat",
    "wooden cane",
    "nail",
    "printer",
    "shovel",
    "CRT monitor",
    "physics textbook",
    "toaster",
    "portrait of Richard Stallman",
    "television",
    "five ton truck",
    "roll of duct tape",
    "book",
    "laptop",
    "old television",
    "sack of rocks",
    "rainbow trout",
    "rubber chicken",
    "spiked bat",
    "fire extinguisher",
    "heavy rock",
    "chunk of dirt",
    "beehive",
    "piece of rotten meat",
    "bear",
    "ton of bricks",
)

THROW = (
    "throws",
    "flings",
    "chucks",
    "hurls",
)

HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks",
    "bashes",
)

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


@run_async
def runs(bot: Bot, update: Update):
    update.effective_message.reply_text(random.choice(RUN_STRINGS))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = f"@{escape_markdown(msg.from_user.username)}"
    else:
        curr_user = f"[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"

    if user_id := extract_user(update.effective_message, args):
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = f"@{escape_markdown(slapped_user.username)}"
        else:
            user2 = f"[{slapped_user.first_name}](tg://user?id={slapped_user.id})"

    else:
        user1 = f"[{bot.first_name}](tg://user?id={bot.id})"
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    if user_id := extract_user(update.effective_message, args):
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                f"The original sender, {escape_markdown(user2.first_name)}, has an ID of `{user2.id}`.\nThe forwarder, {escape_markdown(user1.first_name)}, has an ID of `{user1.id}`.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_text(
                f"{escape_markdown(user.first_name)}'s id is `{user.id}`.",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text(
                f"Your id is `{chat.id}`.", parse_mode=ParseMode.MARKDOWN
            )

        else:
            update.effective_message.reply_text(
                f"This group's id is `{chat.id}`.",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif (
        not msg.reply_to_message
        and len(args) >= 1
        and not args[0].startswith("@")
        and not args[0].isdigit()
        and not msg.parse_entities([MessageEntity.TEXT_MENTION])
    ):
        msg.reply_text("I can't extract a user from this.")
        return

    else:
        return

    del_msg = msg.reply_text(
        "Collecting Data from <b>Database</b>...",
        parse_mode=ParseMode.HTML,
    )

    text = f"<b>USER INFO</b>:\n\nID: <code>{user.id}</code>\nFirst Name: {html.escape(user.first_name)}"

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f'\nPermanent user link: {mention_html(user.id, "link")}'

    text += f"\nNumber of profile pics: {bot.get_user_profile_photos(user.id).total_count}"

    if user.id == OWNER_ID:
        text += "\n\nThis person is my owner.\nI would never do anything against him!"

    elif user.id in SUDO_USERS:
        text += (
            "\n\nThis person is one of my sudo users! "
            "Nearly as powerful as my owner - so watch it."
        )

    elif user.id in SUPPORT_USERS:
        text += (
            "\n\nThis person is one of my support users! "
            "Not quite a sudo user, but can still gban you off the map."
        )

    elif user.id in WHITELIST_USERS:
        text += (
            "\n\nThis person has been whitelisted! "
            "That means I'm not allowed to ban/kick them."
        )

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\n\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    try:
        profile = bot.get_user_profile_photos(user.id).photos[0][-1]
        bot.sendChatAction(chat.id, "upload_photo")
        bot.send_photo(
            chat.id,
            photo=profile,
            caption=(text),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except IndexError:
        bot.sendChatAction(chat.id, "typing")
        msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    finally:
        del_msg.delete()


@run_async
def get_time(bot: Bot, update: Update, args: List[str]):
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        send_message(update.effective_message, "Its always banhammer time for me!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(
        f'https://dev.virtualearth.net/REST/v1/timezone/?query={location}&key={MAPS_API}'
    )

    if res.status_code == 200:
        loc = res.json()
        if len(loc['resourceSets'][0]['resources'][0]['timeZoneAtLocation']) == 0:
            send_message(update.effective_message, tl(update.effective_message, "Location not Found!"))
            return
        placename = loc['resourceSets'][0]['resources'][0]['timeZoneAtLocation'][0]['placeName']
        localtime = loc['resourceSets'][0]['resources'][0]['timeZoneAtLocation'][0]['timeZone'][0]['convertedTime']['localTime']
        time = datetime.strptime(localtime, '%Y-%m-%dT%H:%M:%S').strftime("%H:%M:%S %A, %d %B")
        send_message(update.effective_message, tld(update.effective_message, "It now `{}` in `{}`").format(time, placename), parse_mode="markdown")
    else:
        send_message(update.effective_message, tld(update.effective_message, "Use `/time name place`\nEx: `/time Kolkata`"), parse_mode="markdown")

           
            

@run_async
def echo(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@run_async
def gdpr(bot: Bot, update: Update):
    update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text("Your personal data has been deleted.\n\nNote that this will not unban "
                                        "you from any chats, as that is telegram data, not Marie data. "
                                        "Flooding, warns, and gbans are also preserved, as of "
                                        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
                                        "which clearly states that the right to erasure does not apply "
                                        "\"for the performance of a task carried out in the public interest\", as is "
                                        "the case for the aforementioned pieces of data.",
                                        parse_mode=ParseMode.MARKDOWN)

MARKDOWN_HELP = """
Markdown is a very powerful formatting tool supported by telegram. {} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
""".format(dispatcher.bot.first_name)


@run_async
def markdown_help(bot: Bot, update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text("Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text("/save test This is a markdown test. _italics_, *bold*, `code`, "
                                        "[URL](example.com) [button](buttonurl:github.com) "
                                        "[button2](buttonurl://google.com:same)")

@run_async
def reply_keyboard_remove(bot: Bot, update: Update):
    reply_keyboard = [[ReplyKeyboardRemove(
            remove_keyboard=True
        )]]
    reply_markup = ReplyKeyboardRemove(
        remove_keyboard=True
    )
    old_message = bot.send_message(
        chat_id=update.message.chat_id,
        text='Hmmm, Trying...',
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id
    )
    bot.delete_message(
        chat_id=update.message.chat_id,
        message_id=old_message.message_id
    )


@run_async
def stats(bot: Bot, update: Update):
    update.effective_message.reply_text("Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS]))

@run_async
def stickerid(bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            (
                (
                    f"Hello [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"
                    + ", The sticker id you are replying is :\n```"
                )
                + escape_markdown(msg.reply_to_message.sticker.file_id)
                + "```"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        update.effective_message.reply_text(
            f"Hello [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}), Please reply to sticker message to get id sticker",
            parse_mode=ParseMode.MARKDOWN,
        )
@run_async
def getsticker(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    bot.sendChatAction(chat_id, "typing")
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            (
                f"Hello [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"
                + ", Please check the file you requested below."
                "\nPlease use this feature wisely!"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        bot.sendChatAction(chat_id, "upload_document")
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.sendDocument(chat_id, document=open('sticker.png', 'rb'))
        bot.sendChatAction(chat_id, "upload_photo")
        bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))

    else:
        update.effective_message.reply_text(
            f"Hello [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}), Please reply to sticker message to get sticker image",
            parse_mode=ParseMode.MARKDOWN,
        )

# /ip is for private use
__help__ = """
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /runs: reply a random string from an array of replies.
 - /slap: slap a user, or get slapped if not a reply.
 - /time <place>: gives the local time at the given place.
 - /info: get information about a user.
 - /gdpr: deletes your information from the bot's database. Private chats only.
 - /markdownhelp: quick summary of how markdown works in telegram - ge only be called in private chats.
 - /removebotkeyboard: Got a nasty bot keyboard stuck in your group try this!
"""



__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))

TIME_HANDLER = CommandHandler("time", get_time, pass_args=True)

RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)


dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(DisableAbleCommandHandler("removebotkeyboard", reply_keyboard_remove))
