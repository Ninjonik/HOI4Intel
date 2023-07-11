import discord
from discord.ext import commands
from discord import app_commands
import config
from presets import check_host


class unban(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="unban", description="Unbans user.")
    async def add_record(self, interaction: discord.Interaction, player_discord_id: str, reason: str):
        if check_host(interaction.user.id):
            try:
                player_discord_id = int(player_discord_id)
                user = self.client.get_user(player_discord_id)
            except Exception as e:
                await interaction.response.send_message("❌ Invalid discord ID.")
                return
            self.cursor.execute("SELECT id FROM bans WHERE player_id=%s", (player_discord_id,))
            player_data = self.cursor.fetchone()
            if player_data:
                self.cursor.execute("DELETE FROM bans WHERE player_id=%s", (player_discord_id,))
                message = await interaction.response.send_message("ℹ️ Unbanning user...")
                for guild in self.client.guilds:
                    try:
                        await guild.unban(discord.Object(id=player_discord_id), reason=reason)
                    except Exception as e:
                        print(f"Not enough permissions for unbanning / User not banned | {user.name} on {guild.name}, "
                              f"Host: {interaction.user.name}")
                await message.edit("✔️ User has been unbanned!")
            else:
                try:
                    await interaction.guild.unban(user, reason=reason)
                    await interaction.response.send_message("✔️ User has been unbanned locally.")
                except Exception as e:
                    await interaction.response.send_message("❌ User is not banned.")
                    return

            self.connection.commit()
        else:
            interaction.response.send_message("❌ You don't have enough permissions for this command. (Verified Host+)")



async def setup(client: commands.Bot) -> None:
    await client.add_cog(unban(client))
