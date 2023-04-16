# Claude & Bard Telegram Bot

This is a Telegram bot that intereact with **Anthropic Claude** and **Google Bard**.

Before using this bot, you need to apply for access credentials for Claude and Bard respectively:

- Join waitlists: [Claude](https://www.anthropic.com/earlyaccess/) | [Bard](https://bard.google.com/signup)

- Obtain APIs: [Claude (official)](https://console.anthropic.com/account/keys) | [Bard (reverse engineered)](https://github.com/acheong08/Bard)

If you only have access to one of the models, you can still continue to use this bot. Some functions may be limited due to lack of authorization for the other model.

## Features

- Support of [official Claude API](https://console.anthropic.com/account/keys) and [reverse engineered Bard API](https://github.com/acheong08/Bard)
- Support of partial Markdown
- Claude's streaming output
- Modify [Claude's model (defaults to v1.3) and temperature (defaults to 1)](https://console.anthropic.com/docs/api/reference)
- Show reference links and Google search keywords from Bard's answers
- Switch between different drafts provided by Bard's answers
- [Private chat, group chat, invitation mode, independent chat session](https://github.com/Lakr233/ChatBot-TGLM6B)

|                             Claude                             |                            Bard                            |
| :------------------------------------------------------------: | :--------------------------------------------------------: |
|                   ❌Online - ✅Stream generate                   |                 ✅Online - ❌Stream generate                 |
| <img src="https://user-images.githubusercontent.com/41275670/232324173-6e451359-45be-4e87-a64a-5f485806b3fa.gif" alt="demo_claude" width="288"> | <img src="https://user-images.githubusercontent.com/41275670/232329807-71154441-58f0-4763-ab8b-8d6a74afb270.gif" alt="demo_bard" width="288"> |

## Usage

1. Fill in `config.yml` with reference to `config.example.yml`.

    - [How to obtain telegram bot token](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)
    - [How to obtain telegram user id](https://bigone.zendesk.com/hc/en-us/articles/360008014894-How-to-get-the-Telegram-user-ID-)

2. Run the following command in terminal to create the virtual environment:

    ```bash
    bash setup.sh
    ```

3. To start running the bot, use the following command:

    ```bash
    bash run.sh
    ```

4. To stop the bot, use the following command:

    ```bash
    bash kill.sh
    ```

## Acknowledgements

This code is based on [Lakr233's ChatBot-TGLM6B](https://github.com/Lakr233/ChatBot-TGLM6B).

The client library for Claude API is [anthropics's anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python).

The client library for Bard API is [acheong08's Bard](https://github.com/acheong08/Bard).

Huge thanks to them!!! 🥰🥰🥰

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ciuzaak/Claude-Telegram-Bot&type=Date)](https://star-history.com/#ciuzaak/Claude-Telegram-Bot&Date)
