READY = "READY"
WAITING = "WAITING"
START = "START"
NAME = "NAME"

ATTACK = "ATTACK"
CHAT = "CHAT"
TURN = "TURN"
WAIT_TURN = "WAIT_TURN"
WAIT_ACTION = "WAIT_ACTION"


def format_message(message):
    return f"{message}\n"


def normalize_message(message):
    return message.strip()