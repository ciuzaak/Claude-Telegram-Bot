from re import sub
from urllib.parse import quote

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import bot_token, default_mode, single_mode, user_ids
from utils import Session


def get_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.chat_data.get("mode")
    if mode is None:
        mode = default_mode
        context.chat_data["mode"] = mode
        context.chat_data[mode] = {"session": Session(mode)}
    return mode, context.chat_data[mode]["session"]


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)
    session.reset()
    context.chat_data[mode].pop("last_msg_id", None)
    context.chat_data[mode].pop("last_input", None)
    context.chat_data[mode].pop("seg_message", None)
    context.chat_data[mode].pop("drafts", None)
    await update.message.reply_text("🧹 Chat history has been reset.")


# Google bard: view other drafts
async def view_other_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_msg_id = context.chat_data["Bard"].get("last_msg_id")
    if last_msg_id is not None and update.callback_query.data == f"{last_msg_id}":
        # increase choice index
        context.chat_data["Bard"]["drafts"]["index"] = (
            context.chat_data["Bard"]["drafts"]["index"] + 1
        ) % len(context.chat_data["Bard"]["drafts"]["choices"])
        await bard_response(update, context)


# Google bard: response
async def bard_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.chat_data["Bard"]["session"]
    message, markup, sources, choices, index = context.chat_data["Bard"][
        "drafts"
    ].values()
    session.client.choice_id = choices[index]["id"]
    content = choices[index]["content"][0]
    _content = sub(
        r"[\_\*\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!]", lambda x: f"\\{x.group(0)}", content
    ).replace("\\*\\*", "*")
    _sources = sub(
        r"[\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!]", lambda x: f"\\{x.group(0)}", sources
    )
    try:
        await message.edit_text(
            f"{_content[: 4096 - len(_sources)]}{_sources}",
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except Exception as e:
        if str(e).startswith("Message is not modified"):
            pass
        elif str(e).startswith("Can't parse entities"):
            await message.edit_text(
                f"{content[: 4095 - len(sources)]}.{sources}", reply_markup=markup
            )
        else:
            print(f"[e] {e}")
            await message.edit_text(f"❌ Error orrurred: {e}. /reset")


async def recv_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_text = update.message.text
    if update.message.chat.type != "private":
        if (
            update.message.reply_to_message
            and update.message.reply_to_message.from_user.username
            == context.bot.username
        ):
            pass
        elif update.message.entities is not None and input_text.startswith(
            f"@{context.bot.username}"
        ):
            input_text = input_text.lstrip(f"@{context.bot.username}").lstrip()
        else:
            return
    mode, session = get_session(update, context)

    # handle long message (for claude 100k model)
    seg_message = context.chat_data[mode].get("seg_message")
    if seg_message is None:
        if input_text.startswith("/seg"):
            input_text = input_text.lstrip("/seg").lstrip()
            if input_text.endswith("/seg"):
                input_text = input_text.rstrip("/seg").rstrip()
            else:
                context.chat_data[mode]["seg_message"] = input_text
                return
    else:
        if input_text.endswith("/seg"):
            input_text = f"{seg_message}\n\n{input_text.rstrip('/seg')}".strip()
            context.chat_data[mode].pop("seg_message", None)
        else:
            context.chat_data[mode]["seg_message"] = f"{seg_message}\n\n{input_text}"
            return

    # regenerate the answer
    if input_text.startswith("/retry"):
        last_input = context.chat_data[mode].get("last_input")
        if last_input is None:
            return await update.message.reply_text("❌ Empty conversation.")
        session.revert()
        input_text = input_text.lstrip("/retry").lstrip()
        input_text = input_text or last_input

    if input_text == "":
        return await update.message.reply_text("❌ Empty message.")
    message = await update.message.reply_text("Thinking...")
    context.chat_data[mode]["last_input"] = input_text
    context.chat_data[mode]["last_msg_id"] = message.message_id

    if mode == "Claude":
        prev_response = ""
        for response in session.send_message_stream(input_text):
            response = response[:4096]
            if abs(len(response) - len(prev_response)) < session.cutoff:
                continue
            prev_response = response
            await message.edit_text(response)

        _response = sub(
            r"[\_\*\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!]",
            lambda x: f"\\{x.group(0)}",
            response,
        )
        try:
            await message.edit_text(_response[:4096], parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            if str(e).startswith("Message is not modified"):
                pass
            elif str(e).startswith("Can't parse entities"):
                await message.edit_text(f"{response[:4095]}.")
            else:
                print(f"[e] {e}")
                await message.edit_text(f"❌ Error orrurred: {e}. /reset")

    else:  # Bard
        response = session.send_message(input_text)
        # get source links
        sources = ""
        if response["factualityQueries"]:
            links = set(
                item[2][0].split("//")[-1]
                for item in response["factualityQueries"][0]
                if item[2][0] != ""
            )
            sources = "\n\nSources\n" + "\n".join(
                [f"{i+1}. {val}" for i, val in enumerate(links)]
            )

        # Buttons
        search_url = (
            quote(response["textQuery"][0])
            if response["textQuery"] != ""
            else quote(input_text)
        )
        search_url = f"https://www.google.com/search?q={search_url}"
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="📝 View other drafts",
                        callback_data=f"{message.message_id}",
                    ),
                    InlineKeyboardButton(text="🔍 Google it", url=search_url),
                ]
            ]
        )
        context.chat_data["Bard"]["drafts"] = {
            "message": message,
            "markup": markup,
            "sources": sources,
            "choices": response["choices"],
            "index": 0,
        }
        # get response
        await bard_response(update, context)
        # get images
        if len(response["images"]) != 0:
            media = [
                InputMediaPhoto(image[: image.rfind("=")])
                for image in response["images"]
            ]
            await update.message.reply_media_group(media)


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    infos = [
        f"Mode: <b>{mode}</b>",
    ]
    extras = []
    if mode == "Claude":
        extras = [
            f"Model: <b>{session.model}</b>",
            f"Temperature: <b>{session.temperature}</b>",
            f"Cutoff: <b>{session.cutoff}</b>",
            "",
            "Commands:",
            "• /mode to use Google Bard",
            "• [/model NAME] to change model",
            "• [/temp VALUE] to set temperature",
            "• [/cutoff VALUE] to adjust cutoff",
            "<a href='https://console.anthropic.com/docs/api/reference'>Reference</a>",
        ]
    else:  # Bard
        extras = [
            "",
            "Commands:",
            "• /mode to use Anthropic Claude",
        ]
    infos.extend(extras)
    await update.message.reply_text("\n".join(infos), parse_mode=ParseMode.HTML)


async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if single_mode:
        return await update.message.reply_text(f"❌ You cannot access the other mode.")
    mode, _ = get_session(update, context)

    final_mode, emoji = ("Bard", "🟠") if mode == "Claude" else ("Claude", "🟣")
    context.chat_data["mode"] = final_mode
    if final_mode not in context.chat_data:
        context.chat_data[final_mode] = {"session": Session(final_mode)}
    await update.message.reply_text(
        f"{emoji} Mode has been switched to <b>{final_mode}</b>.",
        parse_mode=ParseMode.HTML,
    )

    last_msg_id = context.chat_data[final_mode].get("last_msg_id")
    if last_msg_id is not None:
        await update.message.reply_text(
            f"☝️ <b>{final_mode}</b>'s last answer. /reset",
            reply_to_message_id=last_msg_id,
            parse_mode=ParseMode.HTML,
        )


async def change_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    if mode == "Bard":
        return await update.message.reply_text("❌ Invalid option for Google Bard.")
    if len(context.args) != 1:
        return await update.message.reply_text("❌ Please provide a model name.")

    model = context.args[0].strip()
    if not session.change_model(model):
        return await update.message.reply_text("❌ Invalid model name.")
    await update.message.reply_text(
        f"🤖 Model has been switched to <b>{model}</b>.", parse_mode=ParseMode.HTML
    )


async def change_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    if mode == "Bard":
        return await update.message.reply_text("❌ Invalid option for Google Bard.")
    if len(context.args) != 1:
        return await update.message.reply_text("❌ Please provide a temperature value.")

    temperature = context.args[0].strip()
    if not session.change_temperature(temperature):
        return await update.message.reply_text("❌ Invalid temperature value.")
    await update.message.reply_text(
        f"🌡️ Temperature has been set to <b>{temperature}</b>.",
        parse_mode=ParseMode.HTML,
    )


async def change_cutoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    if mode == "Bard":
        return await update.message.reply_text("❌ Invalid option for Google Bard.")
    if len(context.args) != 1:
        return await update.message.reply_text("❌ Please provide a cutoff value.")

    cutoff = context.args[0].strip()
    if not session.change_cutoff(cutoff):
        return await update.message.reply_text("❌ Invalid cutoff value.")
    await update.message.reply_text(
        f"✂️ Cutoff has been set to <b>{cutoff}</b>.", parse_mode=ParseMode.HTML
    )


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_strs = [
        "Welcome to <b>Claude & Bard Telegram Bot</b>",
        "",
        "Commands:",
        "• /id to get your chat identifier",
        "• /reset to reset the chat history",
        "• /retry to regenerate the answer",
        "• /seg to send message in segments",
        "• /mode to switch between Claude & Bard",
        "• /settings to show Claude & Bard settings",
    ]
    print(f"[i] {update.effective_user.username} started the bot")
    await update.message.reply_text("\n".join(welcome_strs), parse_mode=ParseMode.HTML)


async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your chat identifier is `{update.effective_chat.id}`, send it to the bot admin to get access\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[e] {context.error}")
    await update.message.reply_text(f"❌ Error orrurred: {context.error}. /reset")


async def post_init(application: Application):
    await application.bot.set_my_commands(
        [
            BotCommand("/reset", "Reset the chat history"),
            BotCommand("/retry", "Regenerate the answer"),
            BotCommand("/seg", "Send message in segments"),
            BotCommand("/mode", "Switch between Claude & Bard"),
            BotCommand("/settings", "Show Claude & Bard settings"),
            BotCommand("/help", "Get help message"),
        ]
    )


def run_bot():
    print(f"[+] bot started, calling loop!")
    application = ApplicationBuilder().token(bot_token).post_init(post_init).build()

    user_filter = filters.Chat(chat_id=user_ids)
    msg_filter = filters.TEXT

    handler_list = [
        CommandHandler("id", send_id),
        CommandHandler("start", start_bot),
        CommandHandler("help", start_bot),
        CommandHandler("reset", reset_chat, user_filter),
        CommandHandler("settings", show_settings, user_filter),
        CommandHandler("mode", change_mode, user_filter),
        CommandHandler("model", change_model, user_filter),
        CommandHandler("temp", change_temperature, user_filter),
        CommandHandler("cutoff", change_cutoff, user_filter),
        MessageHandler(user_filter & msg_filter, recv_msg),
        CallbackQueryHandler(view_other_drafts),
    ]
    for handler in handler_list:
        application.add_handler(handler)
    application.add_error_handler(error_handler)

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
