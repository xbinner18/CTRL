from tg_bot.modules.sql.translation import prev_locale
from tg_bot.modules.translations.English import EnglishStrings
from tg_bot.modules.translations.Russian import RussianStrings
from tg_bot.modules.translations.Ukraine import UkrainianStrings

def tld(chat_id, t, show_none=True):
    LANGUAGE = prev_locale(chat_id)
    print(chat_id, t)
    if LANGUAGE:
        LOCALE = LANGUAGE.locale_name
        if LOCALE in ('ru') and t in RussianStrings:
            return RussianStrings[t]
        elif LOCALE in ('uk') and t in UkrainianStrings:
            return UkrainianStrings[t]
        else:
            return EnglishStrings[t] if t in EnglishStrings else t
    elif show_none:
        return EnglishStrings[t] if t in EnglishStrings else t



def tld_help(chat_id, t):
    LANGUAGE = prev_locale(chat_id)
    print("tld_help ", chat_id, t)
    if LANGUAGE:
        LOCALE = LANGUAGE.locale_name

        t = f"{t}_help"

        print("Test2", t)

        if LOCALE in ('ru') and t in RussianStrings:
            return RussianStrings[t]
        elif LOCALE in ('uk') and t in UkrainianStrings:
            return UkrainianStrings[t]
        else:
            return False
    else:
        return False