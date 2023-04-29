import yaml

# load yaml config
with open("config/config.yml", 'r') as f:
    config_yaml = yaml.safe_load(f)

# config parameters
telegram_token = config_yaml["telegram"]["token"]
telegram_users = config_yaml["telegram"]["users"]
claude_api = config_yaml["claude"]["api"]
bard_api = config_yaml["bard"]["api"]

assert telegram_token is not None and telegram_users is not None
assert claude_api is not None or bard_api is not None

single_mode = claude_api is None or bard_api is None
default_mode = 'claude' if claude_api is not None else 'bard'
