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
        self.cursor, self.connection = config.setup()
        await _add_player_name(interaction.user.id, interaction.user.name, 0.5)
        self.cursor.execute('SELECT steam_id FROM players WHERE discord_id=%s' % interaction.user.id)
        player_db = self.cursor.fetchone()
        if player_db and player_db[0]:
            self.cursor.execute('SELECT verify_role FROM settings WHERE guild_id=%s'
                                % interaction.guild.id)
            guild_db = self.cursor.fetchone()
            try:
                if guild_db and guild_db[0]:
                    role = interaction.guild.get_role(guild_db[0])
                    await interaction.user.add_roles(role, reason="User verified successfully.")
            except:
                print(f"Verify role for guild {interaction.guild.name} not set.")
            await interaction.response.send_message("You have been successfully verified!", ephemeral=True)
        else:
            self.cursor, self.connection = config.setup()
            member = interaction.user
            embed = discord.Embed(title="Steam Verification", description=f"Click on the link below in order to "
                                                                          f"start verification process.",
                                  color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url=member.avatar)
            embed.add_field(name="Link:", value=f"https://hoi.igportals.eu/steam/{member.id}")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(verify(client))
