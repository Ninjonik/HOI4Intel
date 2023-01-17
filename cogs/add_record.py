from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config

class add_record(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    async def _add_player(self, player_id, rating_percentage, current_time):
        try:
            self.cursor.execute(
                "INSERT INTO players (discord_id, rating, created_at, updated_at) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE rating = %s, updated_at = %s",
                (player_id, rating_percentage, current_time, current_time, rating_percentage, current_time))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    @app_commands.command(name="add_record")
    async def add_record(self, interaction: discord.Interaction, player: discord.User, rating: int):
        if interaction.user.guild_permissions.administrator:
            if 0 <= rating <= 100:
                host = interaction.user
                current_time = datetime.now()
                guild = interaction.guild
                rating_percentage = rating / 100
                await self._add_player(host.id, 1, current_time)
                await self._add_player(player.id, rating_percentage, current_time)
                cursor = self.connection.cursor()
                cursor.execute("INSERT INTO player_records (player_id, guild_id, host_id, rating, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)", (player.id, guild.id, host.id, rating_percentage, current_time, current_time))
                self.connection.commit()
                await interaction.response.send_message(f"Player Record for user {player.name} has been successfully created. Previous rating: -")
            else:
                await interaction.response.send_message("Please only enter values in this interval: <0;100>", ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_record(client))
