import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config
from presets import _add_player_name

class help(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name='help', description="Do you need help with commands?")
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(title="Steam Verification", description=f"Click on the link below in order to "
                                                                      f"view **HOI4Intel's Wiki**",
                                  color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=self.client.user.avatar)
        embed.add_field(name="Link:", value=f"https://hoi.theorganization.eu/wiki")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        


async def setup(client: commands.Bot) -> None:
    await client.add_cog(help(client))
