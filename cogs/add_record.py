from datetime import datetime
import discord
from discord.ext import commands
from discord import app_commands
import config
from presets import _add_player_name


class add_record(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="add_record")
    async def add_record(self, interaction: discord.Interaction, player: discord.User, rating: int):
        if interaction.user.guild_permissions.administrator:
            if 0 <= rating <= 100:
                self.cursor, self.connection = config.setup()
                host = interaction.user
                current_time = datetime.now()
                guild = interaction.guild
                rating_percentage = rating / 100
                await interaction.response.send_message("Working on it...", ephemeral=True)
                await _add_player_name(host.id, host.name, 0.5)
                await _add_player_name(player.id, player.name, 0.5)
                cursor = self.connection.cursor()
                cursor.execute(
                    "INSERT INTO player_records (player_id, guild_id, host_id, rating, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (player.id, guild.id, host.id, rating_percentage, current_time, current_time))
                self.connection.commit()

                self.cursor.execute(
                    "SELECT SUM(rating) as SUM, COUNT(rating) AS CNT FROM player_records WHERE player_id=%s" % player.id)
                total = self.cursor.fetchall()
                total_rating = total[0][0] / total[0][1]
                self.cursor.execute("UPDATE players SET rating=%s WHERE discord_id=%s" % (total_rating, player.id))
                self.connection.commit()

                await interaction.channel.send(
                    f"Player Record for user {player.name} has been successfully created. New rating: "
                    f"{total_rating * 100}%")
            else:
                await interaction.channel.send("Please only enter values in this interval: <0;100>",
                                               ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_record(client))
