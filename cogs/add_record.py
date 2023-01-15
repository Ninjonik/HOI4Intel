import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config
import presets


class add_record(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="add_record")
    async def add_record(self, interaction: discord.Interaction, player: discord.User,
                        rating: int):
        await interaction.response.send_message((player.id, rating))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_record(client))
