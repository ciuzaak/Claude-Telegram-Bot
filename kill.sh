ps -ef | grep 'python3 claude_bot.py' | awk '{print $2}' | xargs kill -9
