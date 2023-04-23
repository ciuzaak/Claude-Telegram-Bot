import asyncio
import json
import os
import re
import urllib.parse

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
                      Update)
from telegram.constants import ParseMode
from telegram.ext import (Application, ApplicationBuilder,
                          CallbackQueryHandler, CommandHandler, MessageHandler)

from config import config
from utils.bard_utils import Bard
from utils.claude_utils import Claude


token = config.telegram_token
admin_id = config.telegram_username
fine_granted_identifier = []

# load from fine_granted_identifier.json if exists
try:
    with open('fine_granted_identifier.json', 'r') as f:
        fine_granted_identifier = json.load(f)
except Exception as e:
    pass


chat_context_container = {}


def validate_user(update: Update) -> bool:
    identifier = user_identifier(update)
    return identifier in admin_id or identifier in fine_granted_identifier


def check_should_handle(update: Update, context) -> bool:
    if update.message is None or update.message.text is None or len(update.message.text) == 0:
        return False

    # if is a private chat
    if update.effective_chat.type == 'private':
        return True

    # if replying to ourself
    if (
        True
        and (update.message.reply_to_message is not None)
        and (update.message.reply_to_message.from_user is not None)
        and (update.message.reply_to_message.from_user.id is not None)
        and (update.message.reply_to_message.from_user.id == context.bot.id)
    ):
        return True

    # if mentioning ourself, at the beginning of the message
    if update.message.entities is not None:
        for entity in update.message.entities:
            if (
                True
                and (entity.type is not None)
                and (entity.type == 'mention')
                # and (entity.user is not None)
                # and (entity.user.id is not None)
                # and (entity.user.id == context.bot.id)
            ):
                mention_text = update.message.text[entity.offset:entity.offset + entity.length]
                if not mention_text == f'@{context.bot.username}':
                    continue
                return True

    return False


def user_identifier(update: Update) -> str:
    return f'{update.effective_chat.id}'


def get_chat_session(update: Update, context):
    chat_session = chat_context_container.get(user_identifier(update))
    if chat_session is None:
        chat_session = Claude(id=user_identifier(update))
        context.chat_data['claude'] = {}
        chat_context_container[user_identifier(update)] = chat_session
    return chat_session


async def reset_chat(update: Update, context):
    if not validate_user(update):
        return

    user_id = user_identifier(update)
    if user_id in chat_context_container:
        chat_context_container[user_id].reset()
        await update.message.reply_text('✅ Chat history has been reset.')
    else:
        await update.message.reply_text('❌ Chat history is empty.')


# Google bard: view other drafts
async def view_other_drafts(update: Update, context):
    if update.callback_query.data == 'drafts':
        # increase choice index
        context.chat_data['bard']['index'] = (
            context.chat_data['bard']['index'] + 1) % len(context.chat_data['bard']['choices'])
        await bard_response(**context.chat_data['bard'])


# Google bard: response
async def bard_response(chat_session, message, markup, sources, choices, index):
    chat_session.client.choice_id = choices[index]['id']
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
            chat_session.reset()
            await message.edit_text('❌ Error orrurred, please try again later. Your chat history has been reset.')


# reply. Stream chat for claude
async def recv_msg(update: Update, context):
    if not validate_user(update):
        return
    if not check_should_handle(update, context):
        return
    chat_session = get_chat_session(update, context)

    message = await update.message.reply_text('.')
    if message is None:
        return

    try:
        input_text = update.message.text
        # remove bot name from text with @
        pattern = f'@{context.bot.username}'
        input_text = input_text.replace(pattern, '')

        if chat_session.mode == 'claude':
            cutoff = chat_session.cutoff
            prev_response = ''
            for response in chat_session.send_message_stream(input_text):
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
                    chat_session.reset()
                    await message.edit_text('❌ Error orrurred, please try again later. Your chat history has been reset.')

        else:  # Bard
            loop = asyncio.get_event_loop()  # asynchronous
            response = await loop.run_in_executor(None, chat_session.client.ask, input_text)
            # get source links
            sources = ''
            if response['factualityQueries']:
                links = set(
                    item[2][0] for item in response['factualityQueries'][0] if item[2][0] != '')
                sources = '\n\nSources - Learn More\n' + \
                    '\n'.join([f'{i+1}. {val}' for i, val in enumerate(links)])

            # Buttons
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(response['textQuery'][0]) if response['textQuery'] != '' else urllib.parse.quote(input_text)}"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='📝 View other drafts', callback_data='drafts'),
                                            InlineKeyboardButton(text='🔍 Google it', url=search_url)]])
            context.chat_data['bard'] = {'chat_session': chat_session, 'message': message,
                                         'markup': markup, 'sources': sources, 'choices': response['choices'], 'index': 0}
            # get response
            await bard_response(**context.chat_data['bard'])

    except Exception as e:
        print(f'[e] {e}')
        chat_session.reset()
        await message.edit_text('❌ Error orrurred, please try again later. Your chat history has been reset.')


# Settings
async def show_settings(update: Update, context):
    if not validate_user(update):
        return
    chat_session = get_chat_session(update, context)

    current_mode = chat_session.mode
    infos = [
        f'<b>Current mode:</b> {current_mode}',
    ]
    extras = []
    if current_mode == 'claude':
        extras = [
            f'<b>Current model:</b> {chat_session.model}',
            f'<b>Current temperature:</b> {chat_session.temperature}',
            f'<b>Current cutoff:</b> {chat_session.cutoff}',
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


async def change_mode(update: Update, context):
    if not validate_user(update):
        return
    chat_session = get_chat_session(update, context)

    final_mode = 'bard' if chat_session.mode == 'claude' else 'claude'
    chat_session = Claude(id=user_identifier(
        update), **context.chat_data['claude']) if final_mode == 'claude' else Bard(id=user_identifier(update))
    chat_context_container[user_identifier(update)] = chat_session
    await update.message.reply_text(f'✅ Mode has been switched to {final_mode}.')
    await show_settings(update, context)


async def change_model(update: Update, context):
    if not validate_user(update):
        return
    chat_session = get_chat_session(update, context)

    if chat_session.mode == 'bard':
        await update.message.reply_text('❌ Invalid option for Google Bard.')
        return

    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a model name.')
        return
    model = context.args[0].strip()
    if not chat_session.change_model(model):
        await update.message.reply_text('❌ Invalid model name.')
        return
    context.chat_data['claude']['model'] = model
    await update.message.reply_text(f'✅ Model has been switched to {model}.')
    await show_settings(update, context)


async def change_temperature(update: Update, context):
    if not validate_user(update):
        return
    chat_session = get_chat_session(update, context)

    if chat_session.mode == 'bard':
        await update.message.reply_text('❌ Invalid option for Google Bard.')
        return

    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a temperature value.')
        return
    temperature = context.args[0].strip()
    if not chat_session.change_temperature(temperature):
        await update.message.reply_text('❌ Invalid temperature value.')
        return
    context.chat_data['claude']['temperature'] = float(temperature)
    await update.message.reply_text(f'✅ Temperature has been set to {temperature}.')
    await show_settings(update, context)


async def change_cutoff(update: Update, context):
    if not validate_user(update):
        return
    chat_session = get_chat_session(update, context)

    if chat_session.mode == 'bard':
        await update.message.reply_text('❌ Invalid option for Google Bard.')
        return

    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a cutoff value.')
        return
    cutoff = context.args[0].strip()
    if not chat_session.change_cutoff(cutoff):
        await update.message.reply_text('❌ Invalid cutoff value.')
        return
    context.chat_data['claude']['cutoff'] = int(cutoff)
    await update.message.reply_text(f'✅ Cutoff has been set to {cutoff}.')
    await show_settings(update, context)


async def start_bot(update: Update, context):
    id = user_identifier(update)
    welcome_strs = [
        'Welcome to <b>Claude & Bard Telegram Bot</b>',
        '',
        'Commands:',
        '• /id to get your chat identifier',
        '• /reset to reset the chat history',
        '• /mode to switch between Claude & Bard',
        '• /settings to show Claude & Bard settings',
    ]
    if id in admin_id:
        extra = [
            '',
            'Admin Commands:',
            '• /grant to grant fine-granted access to a user',
            '• /ban to ban a user',
            '• /status to report the status of the bot',
            '• /reboot to clear all chat history',
        ]
        welcome_strs.extend(extra)
    print(f'[i] {update.effective_user.username} started the bot')
    await update.message.reply_text('\n'.join(welcome_strs), parse_mode=ParseMode.HTML)


async def send_id(update: Update, context):
    current_identifier = user_identifier(update)
    await update.message.reply_text(f'Your chat identifier is {current_identifier}, send it to the bot admin to get fine-granted access.')


async def grant(update: Update, context):
    current_identifier = user_identifier(update)
    if current_identifier not in admin_id:
        await update.message.reply_text('❌ You are not admin!')
        return
    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a user id to grant!')
        return
    user_id = context.args[0].strip()
    if user_id in fine_granted_identifier:
        await update.message.reply_text('❌ User already has fine-granted access!')
        return
    fine_granted_identifier.append(user_id)
    with open('fine_granted_identifier.json', 'w') as f:
        json.dump(list(fine_granted_identifier), f)
    await update.message.reply_text('✅ User has been granted fine-granted access!')


async def ban(update: Update, context):
    current_identifier = user_identifier(update)
    if current_identifier not in admin_id:
        await update.message.reply_text('❌ You are not admin!')
        return
    if len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a user id to ban!')
        return
    user_id = context.args[0].strip()
    if user_id in fine_granted_identifier:
        fine_granted_identifier.remove(user_id)
    if user_id in chat_context_container:
        del chat_context_container[user_id]
    with open('fine_granted_identifier.json', 'w') as f:
        json.dump(list(fine_granted_identifier), f)
    await update.message.reply_text('✅ User has been banned!')


async def status(update: Update, context):
    current_identifier = user_identifier(update)
    if current_identifier not in admin_id:
        await update.message.reply_text('❌ You are not admin!')
        return
    report = [
        'Status Report:',
        f'[+] admin users: {admin_id}',
        f'[+] fine-granted users: {len(fine_granted_identifier)}',
        f'[+] chat sessions: {len(chat_context_container)}',
        '',
    ]
    # list each fine-granted user
    cnt = 1
    for user_id in fine_granted_identifier:
        report.append(f'[i] {cnt} {user_id}')
        cnt += 1
    await update.message.reply_text(
        '```\n' + '\n'.join(report) + '\n```',
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def reboot(update: Update, context):
    current_identifier = user_identifier(update)
    if current_identifier not in admin_id:
        await update.message.reply_text('❌ You are not admin!')
        return
    chat_context_container.clear()
    await update.message.reply_text('✅ All chat history has been cleared!')


async def error_handler(update: Update, context):
    print(f'[e] {context.error}')


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand('/reset', 'Reset the chat history'),
        BotCommand('/mode', 'Switch between Claude & Bard'),
        BotCommand('/settings', 'Show Claude & Bard settings'),
        BotCommand('/help', 'Get help message'),
    ])


print(f'[+] bot started, calling loop!')
application = ApplicationBuilder().token(token).post_init(
    post_init).concurrent_updates(True).build()

handler_list = [
    CommandHandler('id', send_id),
    CommandHandler('start', start_bot),
    CommandHandler('help', start_bot),
    CommandHandler('reset', reset_chat),
    CommandHandler('grant', grant),
    CommandHandler('ban', ban),
    CommandHandler('status', status),
    CommandHandler('reboot', reboot),
    CommandHandler('settings', show_settings),
    CommandHandler('mode', change_mode),
    CommandHandler('model', change_model),
    CommandHandler('temp', change_temperature),
    CommandHandler('cutoff', change_cutoff),
    CallbackQueryHandler(view_other_drafts),
    MessageHandler(None, recv_msg),
]
for handler in handler_list:
    application.add_handler(handler)
application.add_error_handler(error_handler)

application.run_polling(drop_pending_updates=True)
