import json

import discord
from discord.ext import commands
from discord import app_commands

import config


class add_player_list(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="add_player_list")
    async def add_player_list(self, interaction: discord.Interaction, event_id: str):
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
            if event and (event["guild_id"] == interaction.guild.id or event["host_id"] == interaction.user.id):

                await interaction.response.send_message("ℹ️ Please enter a country name, ping "
                                                        "player playing this country."
                                                        "\nFormat: @Ninjonik USSR"
                                                        "\nSend 'stop' message when finished.")
                player_list = {}
                while True:
                    # .split(" - ")
                    def check(m):
                        return m.channel == interaction.channel, m.author == interaction.user

                    msg = await self.client.wait_for('message', check=check, timeout=60)
                    if msg.content == 'stop' or not msg.content:
                        break
                    else:
                        try:
                            message = msg.content.split(' ')
                            if not ("<" in message[0] and ">" in message[0] and "@" in message[0]):
                                raise ValueError(f"Invalid player name {message[0]}")
                            player = message[0].replace("<", "").replace(">", "").replace("@", "")
                            country = message[1]
                            await interaction.channel.send("✅ You can continue, send a 'stop' message to stop.")
                            player_list[player] = country
                        except Exception as e:
                            await interaction.channel.send("❓ Invalid input. Example of a valid input: **@Ninjonik "
                                                           "Germany**")
                            print(e)

                self.cursor.execute("UPDATE events SET countries=%s WHERE message_id=%s", (json.dumps(player_list),
                                                                                           event_id,))
                self.connection.commit()
                await interaction.channel.send("✅ Player List has been successfully saved!")

            else:
                await interaction.response.send_message(
                    "❌ The event with this ID does not exist, or you do not have permission to start this event.",
                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_player_list(client))
