import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config
import presets


class setupCommand(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="setup")
    async def setupCommand(self, interaction: discord.Interaction, steam_verification: bool,
                           log_channel: discord.TextChannel,
                           verify_role: discord.Role = None):
        if interaction.user.guild_permissions.administrator:
            guild_id = interaction.guild.id
            guild_name = interaction.guild.name
            guild_count = interaction.guild.member_count
            # Establish database connection
            self.cursor.execute("SELECT guild_id FROM settings WHERE guild_id=%s" % guild_id)
            settings = self.cursor.fetchall()
            current_time = datetime.datetime.now()
            if not settings:
                print(f"{presets.prefix()} Guild was not in database - {guild_name}, adding it")
                self.cursor.execute("INSERT INTO settings (created_at, updated_at, steam_verification, guild_name, "
                                    "guild_id, log_channel, verify_role) VALUES ('%s', "
                                    "'%s', %s, '%s', %s, %s, %s)" % (current_time,
                                                                     current_time, steam_verification, guild_name,
                                                                     guild_id, log_channel.id, verify_role.id))
                self.cursor.execute(
                    "INSERT INTO statistics (guild_id, created_at, updated_at, count) VALUES (%s, '%s', '%s', %s) " % (
                        guild_id, current_time, current_time, guild_count))
                self.connection.commit()
            else:
                self.cursor.execute("UPDATE settings SET updated_at='%s', steam_verification=%s, guild_name='%s', "
                                    "log_channel=%s, verify_role=%s WHERE guild_id=%s" % (current_time,
                                                                                          steam_verification,
                                                                                          guild_name,
                                                                                          log_channel.id,
                                                                                          verify_role.id,
                                                                                          guild_id,))
                self.connection.commit()
            await interaction.response.send_message("Success!", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(setupCommand(client))
