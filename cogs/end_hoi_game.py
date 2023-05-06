import datetime
import json

import discord
from discord.ext import commands
from discord import app_commands
from presets import _add_player_name

import config


class EndHoiGame(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="end_hoi_game")
    async def end_hoi_game(self, interaction: discord.Interaction, event_id: str):
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

                self.cursor.execute("SELECT countries FROM events WHERE message_id=%s", (event_id,))
                data = self.cursor.fetchone()["countries"]
                player_ratings = {}
                if data:
                    countries = json.loads(data)
                    await interaction.response.send_message("ℹ️ To publish results for the game you are required to "
                                                            "first"
                                                            " give rating to all players defined in your playerlist. "
                                                            "(/add_player_list command)")

                    for player, country in countries.items():
                        i = 5
                        while i > 0:
                            i -= 1
                            await interaction.channel.send(f'💹 What is your rating for <@{player}> playing '
                                                           f'{country}? 0-100 (%)')

                            def check(m):
                                return m.channel == interaction.channel, m.author == interaction.user

                            msg = await self.client.wait_for('message', check=check, timeout=60)
                            print(msg)
                            try:
                                rating = int(msg.content)
                                if not 0 <= rating <= 100:
                                    raise ValueError(f"Invalid rating")
                                i = 0
                                await _add_player_name(interaction.user.id, interaction.user.name, 0.5)
                                player = interaction.guild.get_member(int(player))
                                await _add_player_name(player.id, player.name, 0.5)
                                cursor = self.connection.cursor()
                                cursor.execute(
                                    "INSERT INTO player_records (player_id, guild_id, host_id, "
                                    "rating, created_at, updated_at) "
                                    "VALUES (%s, %s, %s, %s, NOW(), NOW())",
                                    (player.id, interaction.guild.id, interaction.user.id, rating / 100))
                                self.connection.commit()

                                self.cursor.execute(
                                    "SELECT SUM(rating) as SUM, COUNT(rating) AS CNT FROM player_records WHERE player_id=%s"
                                    % player.id)
                                total = self.cursor.fetchall()
                                total_rating = total[0]["SUM"] / total[0]["CNT"]
                                self.cursor.execute(
                                    "UPDATE players SET rating=%s WHERE discord_id=%s" % (total_rating, player.id))
                                self.connection.commit()
                                await interaction.channel.send(f"✅ Successfully updated rating for {player.name}, "
                                                               f"new rating: {total_rating * 100}%")
                                player_ratings[player.id] = rating
                            except Exception as e:
                                # TODO: It loops for like 3 times for some reason, gotta fix it
                                if not msg.content:
                                    return
                                print(e)
                                await interaction.channel.send("❌ Please only enter values in this interval: <0;100>")
                                if i == 0:
                                    rating = 50

                    await interaction.channel.send(f"✅ All ratings have been set!")

                embed = discord.Embed(
                    title=f"**{event['title']} event just ended!**",
                    description=event['description'],
                    colour=discord.Colour.green()
                )
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.add_field(
                    name="**Date & Time:**",
                    value=f'<t:{int(datetime.datetime.timestamp(event["created_at"]))}>',
                    inline=False,
                )
                if player_ratings:
                    player_info = [f"<@{user_id}> - {rating}%" for user_id, rating in player_ratings.items()]
                    player_ratings_formatted = "\n".join(player_info)
                    embed.add_field(
                        name="Ratings:",
                        value=player_ratings_formatted, # this is just an example
                        inline=False,
                    )
                embed.set_footer(text=f"Event ID:{event['message_id']}")
                await interaction.guild.get_channel(event["channel_id"]).send(embed=embed)
                event = interaction.guild.get_scheduled_event(event["guild_event_id"])
                await event.end(reason=f"Event has been ended by {interaction.user.name}")
                await interaction.channel.send(f"✅ Event has been ended successfully!")

            else:
                await interaction.response.send_message(
                    "❌ The event with this ID does not exist, or you do not have permission to start this event.",
                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(EndHoiGame(client))
