import discord
from discord.ext import commands
from discord import app_commands

import presets


class guides(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="guides")
    async def roll(self, interaction: discord.Interaction):
        await interaction.response.send_message(content="Please select the guide you want:", view=presets.Select(),
                                                ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(guides(client))
