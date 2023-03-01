import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config
import presets


class setup_custom_channels(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="setup_custom_channels")
    async def setup_custom_channels(self, interaction: discord.Interaction,
                                    temporary_voice_channel: discord.VoiceChannel,
                                    pernament_voice_chanel: discord.VoiceChannel):
        self.cursor, self.connection = config.setup()
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            guild_name = interaction.guild.name
            current_time = datetime.datetime.now()
            self.cursor.execute(
                "UPDATE settings SET updated_at='%s', custom_channel=%s, custom_channel_2=%s WHERE guild_id=%s" % (
                    current_time,
                    temporary_voice_channel.id,
                    pernament_voice_chanel.id,
                    guild_id,))
            self.connection.commit()
            await interaction.response.send_message("Success!", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(setup_custom_channels(client))
