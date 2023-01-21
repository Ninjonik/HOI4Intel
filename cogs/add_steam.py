import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config

class add_steam(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name='add-steam', description="Verify using your steam account.")
    async def add_steam(self, interaction: discord.Interaction):

        member = interaction.user
        roles = [role for role in member.roles]
        embed = discord.Embed(title="Steam Verification", description=f"Click on the link below in order to "
                                                                      f"start verification process.",
                              color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="Link:", value=f"https://hoi.theorganization.eu/steam/{member.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_steam(client))
