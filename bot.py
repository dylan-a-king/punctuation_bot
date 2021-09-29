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


class Bot_Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        await message.channel.send("hello")
        pass


client = Bot_Client()
client.run(TOKEN)
