import discord
from discord.ext import commands
from discord import app_commands
import config
from presets import _add_player_name, check_host, prefix


class ban(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="ban", description="Globally bans user.")
    async def add_record(self, interaction: discord.Interaction, player: discord.User, reason: str):
        if check_host(interaction.user.id):
            self.cursor, self.connection = config.setup()
            self.cursor.execute("SELECT id FROM bans WHERE player_id=%s", (player.id,))
            player_data = self.cursor.fetchone()
            if player_data:
                try:
                    await interaction.guild.ban(player, reason=reason)
                    await interaction.response.send_message("✔️ User has been banned locally.")
                except Exception as e:
                    await interaction.response.send_message("❌ User is already banned.")
            else:
                await _add_player_name(player.id, player.name, 0.5)
                self.cursor.execute("INSERT INTO bans (player_id, guild_id, host_id, reason, created_at, updated_at) "
                                    "VALUES(%s, %s, %s, %s, NOW(), NOW())",
                                    (player.id, interaction.guild.id, interaction.user.id, reason))
                await interaction.response.send_message("ℹ️ Banning user...")
                for guild in self.client.guilds:
                    try:
                        await guild.ban(discord.Object(id=player.id), reason=reason)
                    except Exception as e:
                        print(f"{prefix()} Not enough permissions for banning / User banned | {player.name} on {guild.name}, "
                              f"Host: {interaction.user.name}")
                await interaction.channel.send("✔️ User has been banned!")
            self.connection.commit()
        else:
            interaction.response.send_message("❌ You don't have enough permissions for this command. (Verified Host+)")



async def setup(client: commands.Bot) -> None:
    await client.add_cog(ban(client))
