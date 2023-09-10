import datetime
import discord
from discord.ext import commands
from discord import app_commands

import config


class ClearReservations(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="clear_reservations")
    async def clear_reservations(self, interaction: discord.Interaction, event_id: str):
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
                self.cursor.execute("SELECT event_message_id FROM event_reservations WHERE event_message_id=%s",
                                    (event_id,))
                result = self.cursor.fetchone()

                if result:
                    self.cursor.execute("DELETE FROM event_reservations WHERE event_message_id=%s", (event_id,))
                    self.connection.commit()
                    channel = interaction.guild.get_channel(event["channel_id"])
                    message = await channel.fetch_message(event["message_id"])

                    embed = discord.Embed(
                        title=f"**New event: {event['title']}**",
                        description=event['description'],
                        colour=discord.Colour.green()
                    )
                    embed.set_thumbnail(url=interaction.guild.icon)
                    embed.add_field(
                        name="**Date & Time:**",
                        value=f'<t:{int(datetime.datetime.timestamp(event["event_start"]))}>',
                        inline=False,
                    )
                    embed.add_field(
                        name="Reserve a nation!",
                        value='Click on the "Reserve" button to reserve a nation!',
                        inline=True,
                    )
                    embed.add_field(
                        name="Minimal rating:",
                        value=f'{event["rating_required"] * 100}%',
                        inline=True,
                    )
                    if event['steam_required'] == 1:
                        steam_required = True
                    else:
                        steam_required = False
                    embed.add_field(
                        name="Steam verification required:",
                        value=steam_required,
                        inline=True,
                    )

                    embed.add_field(
                        name="Currently Reserved:",
                        value="",
                        inline=False,
                    )
                    embed.set_footer(text=f"Event ID:{event_id}")
                    await message.edit(embed=embed)

                    await interaction.response.send_message("✅ Reservations were successfully cleared!")
                else:
                    await interaction.response.send_message("❌ No reservations found for this event.")


            else:
                print(event, event_id)
                await interaction.response.send_message(
                    "❌ The event with this ID does not exist, or you do not have permission to modify this event.",
                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ClearReservations(client))
