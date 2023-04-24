import datetime

import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime

import config
from presets import _add_player_name


class start_hoi_game(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="start_hoi_game")
    async def start_hoi_game(self, interaction: discord.Interaction, event_id: int, instructions: str):
        self.cursor, self.connection = config.dictionary_setup()
        if interaction.user.guild_permissions.administrator:
            self.cursor.execute("SELECT * FROM events WHERE message_id=%s", event_id)
            event = self.cursor.fetchone()
            if event["guild_id"] == interaction.guild.id or event["host_id"] == interaction.user.id:
                self.cursor.execute("SELECT * FROM event_reservations WHERE event_message_id=%s", event_id)
                players = self.cursor.fetchall()
                for player in players:
                    try:
                        player = interaction.guild.get_member(player["player_id"])
                        embed = discord.Embed(title=f"📢 {event['title']} has started on {interaction.guild.name}!",
                                              description=f"Hosted by: "
                                                          f"{interaction.guild.get_member(event['host_id'])}",
                                              color=0xff0000)
                        embed.add_field(name="Game has been started!",
                                        value=f"Game {event['title']} has just been started by the host.\n"
                                              f"You were DMed because you have reserved {player['country']} in this "
                                              f"game.",
                                        inline=False)
                        embed.add_field(name="Host's instructions:",
                                        value=instructions,
                                        inline=False)
                        embed.set_footer(text="This is an automatic message, please do not reply to it. "
                                              "If you don't want to receive further announcements "
                                              "about events starting then do not reserve.")
                        await player.create_dm().send(embed=embed)
                    except Exception as e:
                        interaction.response.send_message("There has been an error while processing your request.")
                        print(e)
            else:
                await interaction.response.send_message("Event with this ID does not exist or you do not have the "
                                                        "permission to start this event.", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(start_hoi_game(client))
