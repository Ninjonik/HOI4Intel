import json

import discord
from discord.ext import commands
from discord import app_commands

import config


class clear_player_list(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="clear_player_list")
    async def clear_player_list(self, interaction: discord.Interaction, event_id: str):
        self.cursor, self.connection = config.dictionary_setup()
        try:
            event_id = int(event_id)
        except ValueError:
            await interaction.response.send_message("🔟 Invalid event ID format. Please provide a valid ID.",
                                                    ephemeral=True)
            return
        if interaction.user.guild_permissions.administrator:
            self.cursor.execute("SELECT * FROM events WHERE message_id=%s", (event_id,))
            event = self.cursor.fetchone()
            if event and event["host_id"] == interaction.user.id:

                self.cursor.execute("DELETE FROM events WHERE message_id=%s", (event_id,))

                self.connection.commit()
                await interaction.channel.send("✅ Player List was successfully cleared!")

            else:
                print(event, event_id)
                await interaction.response.send_message(
                    "❌ The event with this ID does not exist, or you do not have permission to modify this event.",
                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(clear_player_list(client))
