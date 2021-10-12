import os
from typing import OrderedDict, Union
from datetime import datetime
# TODO: consider implement scheduling
# import schedule

import discord
from dotenv import load_dotenv

PUNCTUATION_MARKS = [".", "!", "?", ]
PUNCTUATION_AUTHORITY_ROLE_ID = 868196820122210314
# TODO: save this in a file
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

USAGE = f"""```\
USAGE: punct <operation> [args]
a command can have multiple pairs of <operation> [args].
operations:
    {OPS[0]:<28}turns punctuation on in a channel.
    {OPS[1]:<28}turns punctuation off in a channel.
    {OPS[2]:<28}sets the non-punctuator role (i.e.
    {'    ':<28}the role which is exempt from 
    {'    ':<28}punctuation checking) takes the role's
    {'    ':<28}id as an argument.

```"""

# keys are channel ids, values are bools expressing whether referenced channel
# has punctuation turned on
# TODO: save this in a file
punctuating_status = {}

# the id of the non-punctuator role
# TODO: save this in a file
non_punctuator_role = 0

sent_messages_buffer = OrderedDict()

# TODO: make a function that auto-formats log messages; i.e.
# log_format("INFO","The quick brown fox jumped over the lazy dog; little did he realize the harm he'd done.")
# would return: f"{now()}::INFO: The quick brown fox jumped over the\n"
#               f"{'      ':<26} lazy dog; little did he realize the\n"
#               f"{'      ':<26} harm he'd done.
# properly aligned and line-wrapped.


def now() -> str:
    return datetime.now().strftime('%Y:%m:%d::%I:%M%p')


def add_to_buffer(src: discord.Message, reply: discord.Message):
    global sent_messages_buffer
    sent_messages_buffer[src.id] = reply
    if len(sent_messages_buffer) > 10:
        sent_messages_buffer.popitem(last=False)


def is_punctuating(ch: discord.TextChannel) -> bool:
    return punctuating_status[ch.id]


def is_command(msg) -> bool:
    return False if (
        msg.content == ""
    ) else (
        msg.content.split()[0] == COMMAND_PREFIX
    )


def has_permissions(author: discord.Member) -> bool:
    return (
        PUNCTUATION_AUTHORITY_ROLE_ID in [role.id for role in author.roles] or
        author.guild_permissions.administrator
    )


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

    if len(cmd) == 0:
        return USAGE

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
                    return (
                        f"ERROR: argument to set-non-punctuator-role invalid! "
                        f"\"{op[1]}\" cannot be interpereted as a role id!"
                    )

    assert False, "Unreachable: exec_command should always return a message."


class Bot_Client(discord.Client):
    async def on_ready(self):
        print(f'{now()}::STARTUP: Logged on as {self.user}!')

    async def on_message(self, message):
        # don't respond to ourself
        if message.author == self.user:
            return

        # initalize unseen channels
        if message.channel.id not in punctuating_status:
            if 'bot' in message.channel.name:
                punctuating_status[message.channel.id] = False
            else:
                punctuating_status[message.channel.id] = True

        # skip empty messages
        if message.content == "":
            return

        # skip messages with embeds
        # TODO: fix this so that it still corrects
        # the message's content if it's not just the link.
        if len(message.embeds) > 0:
            return

        # handle commands
        if is_command(message):
            result = exec_command(message)
            reply = await message.reply(result)
            await reply.delete(delay=10)
            return

        # perform punctuation checking
        if (is_punctuating(message.channel) and
            non_punctuator_role not in [
            role.id for role in message.author.roles]
            ):
            # TODO: this could be improved to be smarter.
            # For example, maybe add skips for emoji-only messages, etc.
            has_punctuation = message.content[-1] in PUNCTUATION_MARKS
            if not has_punctuation:
                add_to_buffer(
                    message,
                    await message.reply(
                        f"{message.author.display_name}, please behave"
                        " neighborly in this chat by using punctuation."
                    )
                )
                print(
                    f"{now()}::INFO: Flagged a message without punctuation."
                )

    async def on_message_edit(self, before_msg, after_msg):
        # If a message is edited and I replied to it before
        # it was edited, delete my reply and re-process it.
        if before_msg.id in sent_messages_buffer:
            my_reply = sent_messages_buffer[before_msg.id]
            await my_reply.delete()
            print(
                f"{now()}::INFO: A message I replied to was edited!\n"
                f"{'      ':<26} Deleted my response."
            )
        await self.on_message(after_msg)

    async def on_message_delete(self, message):
        if message.id in sent_messages_buffer:
            my_reply = sent_messages_buffer[message.id]
            try:
                await my_reply.delete()
            except discord.errors.NotFound:
                # if my reply was already deleted through the edit system, don't
                # try re-deleting it.
                print(
                    f"{now()}::INFO: Tried to delete my reply to a message,\n "
                    f"{'      ':<26} but it was already deleted."
                )
                pass


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
