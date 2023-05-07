import discord
from discord.ext import commands
from discord import app_commands

import config

class StartHOIGame(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="start_hoi_game")
    async def start_hoi_game(self, interaction: discord.Interaction, event_id: str, instructions: str):
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
            if event and event["started"] == 0 \
                    and (event["guild_id"] == interaction.guild.id or event["host_id"] == interaction.user.id):
                self.cursor.execute("SELECT * FROM event_reservations WHERE event_message_id=%s", (event_id,))
                players = self.cursor.fetchall()
                lobby_channel = interaction.guild.get_channel(event["voice_channel_id"])
                if players:
                    for player in players:
                        try:
                            player_discord = interaction.guild.get_member(player["player_id"])

                            embed = discord.Embed(
                                title=f"📢 {event['title']} has just been started on {interaction.guild.name}!",
                                description=f"Hosted by: {interaction.guild.get_member(event['host_id'])}",
                                color=0x00ff00
                            )
                            embed.add_field(
                                name="Game has been started!",
                                value=f"Game {event['title']} has just been started by the host.\n"
                                      f"You were DMed because you have reserved **{player['country']}** in this game.",
                                inline=False
                            )
                            embed.add_field(
                                name="Lobby VC:",
                                value=lobby_channel.mention,
                                inline=False
                            )
                            embed.add_field(
                                name="Host's instructions:",
                                value=instructions,
                                inline=False
                            )
                            embed.set_footer(
                                text="🤖 This is an automatic message, please do not reply to it.\n"
                                     "If you don't want to receive further announcements about events starting then do "
                                     "not reserve."
                            )

                            channel = await player_discord.create_dm()
                            await channel.send(embed=embed)
                        except Exception as e:
                            await interaction.response.send_message("❌ An error occurred while processing your request.",
                                                                    ephemeral=True)
                            print(e)
                            return
                event = interaction.guild.get_scheduled_event(event["guild_event_id"])
                await event.start(reason=f"Event has been started by {interaction.user.name}")
                self.cursor.execute("UPDATE events SET started=1, updated_at=NOW() WHERE message_id=%s",
                                    (event_id,))
                self.connection.commit()
                self.connection.close()
                await interaction.channel.send(f"✅ Event has been started successfully!")

            else:
                await interaction.response.send_message(
                    "❌ The event with this ID does not exist, or you do not have permission to start this event, "
                    "or the event already started.",
                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(StartHOIGame(client))
