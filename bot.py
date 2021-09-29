import os

import discord
from dotenv import load_dotenv


def get_token() -> str:
    """ Get the token from the ".env" file. """
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    assert DISCORD_TOKEN is not None, "Unable to find discord token in \".env\"."
    return DISCORD_TOKEN


TOKEN = get_token()
PUNCTUATION_MARKS = [".", "!", "?", ]


class Bot_Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        # don't respond to ourself
        if message.author == self.user:
            return

        content = message.content
        has_punctuation = (content[-1] in PUNCTUATION_MARKS)
        if not has_punctuation:
            await message.channel.send("Please use punctuation.")
        pass


client = Bot_Client()
client.run(TOKEN)
