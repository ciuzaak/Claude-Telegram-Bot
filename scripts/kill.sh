ps -ef | grep 'python3 bot.py' | awk '{print $2}' | xargs kill -9
