import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config
import presets


class setupann(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="setupann")
    async def setupann(self, interaction: discord.Interaction, announcement_role: discord.Role):
        self.cursor, self.connection = config.setup()
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            guild_name = interaction.guild.name
            current_time = datetime.datetime.now()
            self.cursor.execute("UPDATE settings SET updated_at='%s', ann_role=%s WHERE guild_id=%s" % (current_time,
                                                                                                        announcement_role.id,
                                                                                                        guild_id,))
            self.connection.commit()
            await interaction.response.send_message("Success!", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(setupann(client))
