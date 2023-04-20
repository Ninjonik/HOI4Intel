import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config
from presets import _add_player_name

class verify(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name='verify', description="Verify using your steam account.")
    async def verify(self, interaction: discord.Interaction):

        await _add_player_name(interaction.user.id, interaction.user.name, 0.5)

        self.cursor.execute('SELECT * FROM players WHERE discord_id=%s' % interaction.user.id)
        player_db = self.cursor.fetchone()
        if player_db[1]:
            self.cursor.execute('SELECT verify_role FROM settings WHERE guild_id=%s'
                                % interaction.guild.id)
            guild_db = self.cursor.fetchone()
            if guild_db[0]:
                role = interaction.guild.get_role(guild_db[0])
                await interaction.user.add_roles(role, reason="User verified successfully.")
            await interaction.response.send_message("You have been successfully verified!", ephemeral=True)
        else:
            self.cursor, self.connection = config.setup()
            member = interaction.user
            roles = [role for role in member.roles]
            embed = discord.Embed(title="Steam Verification", description=f"Click on the link below in order to "
                                                                          f"start verification process.",
                                  color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url=member.avatar)
            embed.add_field(name="Link:", value=f"https://hoi.theorganization.eu/steam/{member.id}")
            await interaction.response.send_message(embed=embed, ephemeral=True)



async def setup(client: commands.Bot) -> None:
    await client.add_cog(verify(client))
