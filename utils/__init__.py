from .bard_utils import Bard
from .claude_utils import Claude


def Session(mode):
    return Claude() if mode == "Claude" else Bard()
