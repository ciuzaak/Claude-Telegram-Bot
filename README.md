# Claude & Bard Telegram Bot

This is a Telegram bot that intereacts with **Anthropic Claude** and **Google Bard**.

Before using this bot, you need to apply for access credentials for Claude and Bard respectively:

- Join waitlists: [Claude](https://www.anthropic.com/earlyaccess/) | [Bard](https://bard.google.com/signup)

- Obtain APIs: [Claude (official)](https://console.anthropic.com/account/keys) | [Bard (reverse engineered)](https://github.com/acheong08/Bard)

If you only have access to one of the models, you can still continue to use this bot. Some functions may be limited due to lack of authorization for the other model.

## Features

- Support of [official Claude API](https://console.anthropic.com/account/keys) and [reverse engineered Bard API](https://github.com/acheong08/Bard)
- Support of partial Markdown formatting
- Send extremely long inputs in segments
- Resend the question and regenerate the answer
- Private chat, group chat, independent chat session
- **Claude only**:
  - Streaming output
  - Modify model's version (**including 100k**) and temperature
- **Bard only**:
  - Toogle between different draft responses
  - View reference links and Google Search keywords
  - View images from Google Search

|                                                                     Claude                                                                      |                                                             Bard                                                              |
| :---------------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------: |
|                                       ✅ Non-English <br> ✅ Streaming output <br> ❌ Access to the Internet                                       |                              ❌ Non-English <br> ❌ Streaming output <br> ✅ Access to the Internet                              |
| <img src="https://user-images.githubusercontent.com/41275670/234178910-422cc3cd-b1bf-4c06-bc51-7c75c0b71b35.gif" alt="demo_claude" width="288"> | <img src="https://user-images.githubusercontent.com/41275670/234179231-ed955dec-a75c-432f-9ec1-44c419998ffd.gif" width="288"> |

## Getting Started

### [Deployment (Zeabur)](https://github.com/ciuzaak/Claude-Telegram-Bot/issues/10#issue-1717101083)

### Deployment (Local)

1. Clone this repository.

2. Configure the bot in the following two ways:
   1. **Create `config/config.yml`** and fill in the information with reference to `config/config.example.yml`.
   2. or **Set environment variables:**

      ```bash
      export BOT_TOKEN="your bot token"
      export USER_IDS="user_id1,user_id2,..."
      export CLAUDE_API="your claude api" # ignore it if you don't want to use claude
      export BARD_API="your bard api" # ignore it if you don't want to use bard
      ```

    - [How to obtain telegram bot token](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)
    - [How to obtain telegram user id](https://bigone.zendesk.com/hc/en-us/articles/360008014894-How-to-get-the-Telegram-user-ID-)

3. Start the bot in the following two ways:
    1. **Docker** (with docker engine pre-installed):

        ```bash
        docker compose up
        ```

    2. or **Scripts** (with python >= 3.8 and python3-venv pre-installed):

        ```bash
        # create the virtual environment
        bash scripts/setup.sh

        # start the bot
        bash scripts/run.sh
        ```

### Usage

#### Commands

- `/id`: get your chat identifier
- `/start`: start the bot and get help message
- `/help`: get help message
- `/reset`: reset the chat history
- `/settings`: show Claude & Bard settings
- `/mode`: switch between Claude and Bard
- `/model NAME`: change model (**Claude only**)
  - **Options:**
            claude-1,
            claude-1-100k,
            claude-instant-1,
            claude-instant-1-100k,
            claude-1.3,
            claude-1.3-100k,
            claude-1.2,
            claude-1.0,
            claude-instant-1.1,
            claude-instant-1.1-100k,
            claude-instant-1.0
- `/temp VALUE`: set temperature (**Claude only**)
  - **Range:** float in [0, 1]
  - **Impact:** amount of randomness injected into the response
  - **Suggestion:** temp closer to 0 for analytical / multiple choice, and temp closer to 1 for creative and generative tasks
- `/cutoff VALUE`: adjust cutoff (**Claude only**)
  - **Range:** int > 0
  - **Impact:**: smaller cutoff indicates higher frequency of streaming output
  - **Suggestion:** 50 for private chat, 150 for group chat
- `/seg`: send messages in segments, suitable for Claude's 100k models, example below:
    1. Send `/seg` first
    2. Paste a long text and send (or send a series of text in segments)
    3. Input your other questions and send
    4. Send `/seg` again
    5. Bot will respond and you can continue the conversation
- `/retry`: regenerate the answer. Use `/retry TEXT` to modify your last input.

#### Others

- `📝 View other drafts`: click to see other drafts (**Bard Only**)
- `🔍 Google it`: click to view the search results (**Bard Only**)

## Acknowledgements

This code is based on [Lakr233's ChatBot-TGLM6B](https://github.com/Lakr233/ChatBot-TGLM6B).

The client library for Claude API is [anthropics's anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python).

The client library for Bard API is [acheong08's Bard](https://github.com/acheong08/Bard).

Huge thanks to them!!! 🥰🥰🥰
