import yaml

# load yaml config
with open("config/config.yml", 'r') as f:
    config_yaml = yaml.safe_load(f)

# config parameters
telegram_token = config_yaml["telegram"]["token"]
telegram_username = config_yaml["telegram"]["username"]
claude_api = config_yaml["claude"]["api"]
bard_api = config_yaml["bard"]["api"]
