import os
from typing import Union

# TODO: consider implement scheduling
# import schedule

import discord
from dotenv import load_dotenv

PUNCTUATION_MARKS = [".", "!", "?", ]
PUNCTUATION_AUTHORITY_ROLE_ID = 0
non_punctuator_role = 0
COMMAND_PREFIX = "punct"

OPS = [
    "on",
    "off",
    "set-non-punctuator-role",
]

assert len(OPS) == 3, "Exhaustive op handling in OP_ARG_AMTS"
OP_ARG_AMTS = {
    "on": 0,
    "off": 0,
    "set-non-punctuator-role": 1,
}

# keys are channel ids, values are bools expressing whether referenced channel
# has punctuation turned on
punctuating_status = {}

# the id of the non-punctuator role
non_punctuator_role = 0


def is_punctuating(ch: discord.TextChannel) -> bool:
    return punctuating_status[ch.id]


def is_command(msg) -> bool:
    return msg.content.split()[0] == COMMAND_PREFIX


def has_permissions(author: discord.Member) -> bool:
    return any((PUNCTUATION_AUTHORITY_ROLE_ID in author.roles,
               author.guild_permissions.administrator))


def lex_command(content: str) -> list[Union[str, list[str]]]:
    # remove prefix and seperate command into words
    words: list[str] = content.split()[1:]

    # build up a list of grouped words, args grouped with ops
    cmd: list[Union[str, list[str]]] = []
    for idx, word in enumerate(words):
        if word in OPS:
            arg_amt = OP_ARG_AMTS[word]
            if arg_amt == 0:
                cmd.append(word)
            else:
                cmd.append(words[idx: idx + 1 + arg_amt])
        else:
            # TODO: check if all words have been consumed rather than ignoring
            #       unused words.
            ...
    return cmd


def exec_command(msg: discord.message) -> str:
    global non_punctuator_role
    # lex command
    cmd = lex_command(msg.content)

    # TODO: fix command parsing errors i.e. send the error to the user
    if not has_permissions(msg.author):
        return "ERROR: you do not have proper perms!"

    assert len(OPS) == 3, "Exhaustive op handling in exec_command"
    for op in cmd:
        if isinstance(op, str):
            if op == "on":
                punctuating_status[msg.channel.id] = True
                return f"INFO: Punctuating is on for #{msg.channel.name}"
            if op == "off":
                punctuating_status[msg.channel.id] = False
                return f"INFO: Puncuating is off for #{msg.channel.name}"
        else:
            if op[0] == "set-non-punctuator-role":
                try:
                    non_punctuator_role = int(op[1])
                    return f"INFO: Set non-punctuator role to role-id#{op[1]}"
                except ValueError:
                    return f"ERROR: argument to set-non-punctuator-role invalid! " \
                        f"\"{op[1]}\" cannot be interpereted as a role id!"


class Bot_Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        # don't respond to ourself
        if message.author == self.user:
            return

        # initalize unseen channels
        if message.channel.id not in punctuating_status:
            punctuating_status[message.channel.id] = True

        if is_command(message):
            result = exec_command(message)
            await message.reply(result)
            return

        if is_punctuating(message.channel) and \
                non_punctuator_role not in [role.id for role in message.author.roles]:
            has_punctuation = message.content[-1] in PUNCTUATION_MARKS
            if not has_punctuation:
                await message.reply(
                    f"{message.author.display_name}, please behave neighborly "
                    "in this chat, and use punctuation."
                )


def get_token() -> str:
    """ Get the token from the ".env" file. """
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    assert DISCORD_TOKEN is not None, (
        "Unable to find discord token in \".env\"."
    )
    return DISCORD_TOKEN


TOKEN = get_token()

client = Bot_Client()
client.run(TOKEN)
