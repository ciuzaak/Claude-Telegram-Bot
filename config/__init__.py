from yaml import safe_load

# load yaml config
with open('config/config.yml', 'r') as f:
    config_yaml = safe_load(f)

# config parameters
bot_token = config_yaml['telegram']['bot_token']
user_ids = config_yaml['telegram']['user_ids']
claude_api = config_yaml['claude']['api']
bard_api = config_yaml['bard']['api']

assert bot_token is not None and user_ids is not None
assert claude_api is not None or bard_api is not None

single_mode = claude_api is None or bard_api is None
default_mode = 'Claude' if claude_api is not None else 'Bard'
