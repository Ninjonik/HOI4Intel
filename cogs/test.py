import discord
from discord.ext import commands
from discord import app_commands
import presets


class test(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="test", description="Runs the current test command!")
    async def test(self, interaction: discord.Interaction):
        guild = await self.client.fetch_guild(820918304176340992)
        print(guild)
        await interaction.response.send_message("YES")



async def setup(client: commands.Bot) -> None:
    await client.add_cog(test(client))
