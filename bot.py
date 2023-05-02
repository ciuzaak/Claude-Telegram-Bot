import asyncio
import re
from urllib.parse import quote

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
                      Update)
from telegram.constants import ParseMode
from telegram.ext import (Application, ApplicationBuilder,
                          CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

import config
from utils import Session


def get_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.chat_data.get('mode')
    if mode is None:
        mode = config.default_mode
        context.chat_data['mode'] = mode
        context.chat_data[mode] = {'session': Session(mode)}
    return mode, context.chat_data[mode]['session']


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)
    session.reset()
    context.chat_data[mode].pop('last_message', None)
    context.chat_data[mode].pop('drafts', None)
    await update.message.reply_text('🧹 Chat history has been reset.')


# Google bard: view other drafts
async def view_other_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_message = context.chat_data['Bard'].get('last_message')
    if last_message is not None and update.callback_query.data == f'{last_message}':
        # increase choice index
        context.chat_data['Bard']['drafts']['index'] = (
            context.chat_data['Bard']['drafts']['index'] + 1) % len(context.chat_data['Bard']['drafts']['choices'])
        await bard_response(update, context)


# Google bard: response
async def bard_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.chat_data['Bard']['session']
    message, markup, sources, choices, index = context.chat_data['Bard']['drafts'].values(
    )
    session.client.choice_id = choices[index]['id']
    content = choices[index]['content'][0]
    _content = re.sub(
        r'[\_\*\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!]', lambda x: f'\\{x.group(0)}', content).replace('\\*\\*', '*')
    _sources = re.sub(
        r'[\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!]', lambda x: f'\\{x.group(0)}', sources)
    try:
        await message.edit_text(f'{_content}{_sources}', reply_markup=markup, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        if str(e).startswith('Message is not modified'):
            await message.edit_text(f'{_content}{_sources}\\.', reply_markup=markup, parse_mode=ParseMode.MARKDOWN_V2)
        elif str(e).startswith("Can't parse entities"):
            await message.edit_text(f'{content}{sources}', reply_markup=markup)
        elif str(e).startswith('Message is too long'):
            await message.edit_text(content[:4096], reply_markup=markup)
        else:
            print(f'[e] {e}')
            await message.edit_text('❌ Error orrurred, please try again later.')
            await reset_chat(update, context)


async def recv_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)
    message = await update.message.reply_text('.')
    context.chat_data[mode]['last_message'] = message.message_id

    try:
        input_text = update.message.text
        # remove bot name from text with @
        input_text = input_text.replace(f'@{context.bot.username}', '')

        if mode == 'Claude':
            cutoff = session.cutoff
            prev_response = ''
            for response in session.send_message_stream(input_text):
                if abs(len(response) - len(prev_response)) < cutoff:
                    continue
                prev_response = response
                await message.edit_text(response)

            _response = re.sub(
                r'[\_\*\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!]', lambda x: f'\\{x.group(0)}', response)
            try:
                await message.edit_text(_response, parse_mode=ParseMode.MARKDOWN_V2)
            except Exception as e:
                if str(e).startswith('Message is not modified'):
                    await message.edit_text(f'{_response}\\.', parse_mode=ParseMode.MARKDOWN_V2)
                elif str(e).startswith("Can't parse entities"):
                    await message.edit_text(response)
                elif str(e).startswith('Message is too long'):
                    await message.edit_text(response[:4096])
                else:
                    print(f'[e] {e}')
                    await message.edit_text('❌ Error orrurred, please try again later.')
                    await reset_chat(update, context)

        else:  # Bard
            loop = asyncio.get_event_loop()  # asynchronous
            response = await loop.run_in_executor(None, session.client.ask, input_text)
            # get source links
            sources = ''
            if response['factualityQueries']:
                links = set(
                    item[2][0] for item in response['factualityQueries'][0] if item[2][0] != '')
                sources = '\n\nSources - Learn More\n' + \
                    '\n'.join([f'{i+1}. {val}' for i, val in enumerate(links)])

            # Buttons
            search_url = f"https://www.google.com/search?q={quote(response['textQuery'][0]) if response['textQuery'] != '' else quote(input_text)}"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='📝 View other drafts', callback_data=f'{message.message_id}'),
                                            InlineKeyboardButton(text='🔍 Google it', url=search_url)]])
            context.chat_data['Bard']['drafts'] = {
                'message': message, 'markup': markup, 'sources': sources, 'choices': response['choices'], 'index': 0}
            # get response
            await bard_response(update, context)

    except Exception as e:
        print(f'[e] {e}')
        await message.edit_text('❌ Error orrurred, please try again later.')
        await reset_chat(update, context)


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    infos = [
        f'Mode: <b>{mode}</b>',
    ]
    extras = []
    if mode == 'Claude':
        extras = [
            f'Model: <b>{session.model}</b>',
            f'Temperature: <b>{session.temperature}</b>',
            f'Cutoff: <b>{session.cutoff}</b>',
            '',
            'Commands:',
            '• /mode to use Google Bard',
            '• [/model NAME] to change model',
            '• [/temp VALUE] to set temperature',
            '• [/cutoff VALUE] to adjust cutoff',
            "<a href='https://console.anthropic.com/docs/api/reference'>Reference</a>",
        ]
    else:  # Bard
        extras = [
            '',
            'Commands:',
            '• /mode to use Anthropic Claude',
        ]
    infos.extend(extras)
    await update.message.reply_text('\n'.join(infos), parse_mode=ParseMode.HTML)


async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.single_mode:
        await update.message.reply_text(f'❌ You cannot access the other mode.')
        return
    mode, _ = get_session(update, context)

    final_mode, emoji = ('Bard', '🟠') if mode == 'Claude' else ('Claude', '🟣')
    context.chat_data['mode'] = final_mode
    if final_mode not in context.chat_data:
        context.chat_data[final_mode] = {'session': Session(final_mode)}
    await update.message.reply_text(f'{emoji} Mode has been switched to <b>{final_mode}</b>.',
                                    parse_mode=ParseMode.HTML)

    last_message = context.chat_data[final_mode].get('last_message')
    if last_message is not None:
        await update.message.reply_text(f"☝️ <b>{final_mode}</b>'s last answer. /reset",
                                        reply_to_message_id=last_message, parse_mode=ParseMode.HTML)


async def change_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    if mode == 'Bard':
        await update.message.reply_text('❌ Invalid option for Google Bard.')
        return

    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a model name.')
        return
    model = context.args[0].strip()
    if not session.change_model(model):
        await update.message.reply_text('❌ Invalid model name.')
        return
    await update.message.reply_text(f'🤖 Model has been switched to <b>{model}</b>.',
                                    parse_mode=ParseMode.HTML)


async def change_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    if mode == 'Bard':
        await update.message.reply_text('❌ Invalid option for Google Bard.')
        return

    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a temperature value.')
        return
    temperature = context.args[0].strip()
    if not session.change_temperature(temperature):
        await update.message.reply_text('❌ Invalid temperature value.')
        return
    await update.message.reply_text(f'🌡️ Temperature has been set to <b>{temperature}</b>.',
                                    parse_mode=ParseMode.HTML)


async def change_cutoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode, session = get_session(update, context)

    if mode == 'Bard':
        await update.message.reply_text('❌ Invalid option for Google Bard.')
        return

    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a cutoff value.')
        return
    cutoff = context.args[0].strip()
    if not session.change_cutoff(cutoff):
        await update.message.reply_text('❌ Invalid cutoff value.')
        return
    await update.message.reply_text(f'✂️ Cutoff has been set to <b>{cutoff}</b>.',
                                    parse_mode=ParseMode.HTML)


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_strs = [
        'Welcome to <b>Claude & Bard Telegram Bot</b>',
        '',
        'Commands:',
        '• /id to get your chat identifier',
        '• /reset to reset the chat history',
        '• /mode to switch between Claude & Bard',
        '• /settings to show Claude & Bard settings',
    ]
    print(f'[i] {update.effective_user.username} started the bot')
    await update.message.reply_text('\n'.join(welcome_strs), parse_mode=ParseMode.HTML)


async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Your chat identifier is `{update.effective_chat.id}`, send it to the bot admin to get access\\.',
                                    parse_mode=ParseMode.MARKDOWN_V2)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'[e] {context.error}')


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand('/reset', 'Reset the chat history'),
        BotCommand('/mode', 'Switch between Claude & Bard'),
        BotCommand('/settings', 'Show Claude & Bard settings'),
        BotCommand('/help', 'Get help message'),
    ])


def run_bot():
    print(f'[+] bot started, calling loop!')
    application = ApplicationBuilder().token(config.bot_token).post_init(
        post_init).concurrent_updates(True).build()

    user_filter = filters.Chat(chat_id=config.user_ids)
    message_filter = filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE | (
        filters.ChatType.GROUPS & filters.REPLY | (filters.Entity('mention') & filters.Regex(f'@{config.bot_name}')))

    handler_list = [
        CommandHandler('id', send_id),
        CommandHandler('start', start_bot),
        CommandHandler('help', start_bot),
        CommandHandler('reset', reset_chat, user_filter),
        CommandHandler('settings', show_settings, user_filter),
        CommandHandler('mode', change_mode, user_filter),
        CommandHandler('model', change_model, user_filter),
        CommandHandler('temp', change_temperature, user_filter),
        CommandHandler('cutoff', change_cutoff, user_filter),
        MessageHandler(message_filter & user_filter, recv_msg),
        CallbackQueryHandler(view_other_drafts),
    ]
    for handler in handler_list:
        application.add_handler(handler)
    application.add_error_handler(error_handler)

    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    run_bot()
