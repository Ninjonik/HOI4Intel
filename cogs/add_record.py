import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config


class add_record(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="add_record")
    async def add_record(self, interaction: discord.Interaction, player: discord.User,
                         rating: int):
        if interaction.user.guild_permissions.administrator:
            if 0 <= rating <= 100:
                host = interaction.user
                current_time = datetime.datetime.now()
                self.cursor.execute("SELECT rating FROM players WHERE discord_id = %s" % interaction.user.id)
                host_rating = self.cursor.fetchone()
                if not host_rating:
                    self.cursor.execute("INSERT INTO players (discord_id, rating, created_at, "
                                        "updated_at) "
                                        "VALUES (%s, %s, '%s', '%s')" % (host.id, 1,
                                                                         current_time, current_time))
                    self.connection.commit()

                guild = interaction.guild
                rating_percentage = rating / 100
                self.cursor.execute("SELECT rating FROM players WHERE discord_id = %s" % player.id)
                player_rating = self.cursor.fetchone()
                if not player_rating:
                    self.cursor.execute("INSERT INTO players (discord_id, rating, created_at, "
                                        "updated_at) "
                                        "VALUES (%s, %s, '%s', '%s')" % (player.id, rating_percentage,
                                                                         current_time, current_time))
                    self.connection.commit()

                self.cursor.execute("INSERT INTO player_records (player_id, guild_id, host_id, rating, "
                                    "created_at, "
                                    "updated_at) "
                                    "VALUES (%s, %s, %s, %s, '%s', '%s')" % (player.id, guild.id, host.id,
                                                                             rating_percentage, current_time,
                                                                             current_time))
                self.connection.commit()
                await interaction.response.send_message(f"Player Record for user {player.name} has been "
                                                        f"successfully created. Previous rating: -")

            else:
                interaction.response.send_message("Please only enter values in this interval: <0;100>", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_record(client))
