import datetime
import discord
from discord.ext import commands
from discord import app_commands
import config
import presets
import pytz


class add_hoi_game(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="add_hoi_game", description="Schedule a new HOI4 Game with reservation!")
    @app_commands.describe(lobby_vc="Lobby Voice Channel where the game will be hosted",
                           date_time="Example: Day.Month.Year Hours:Minutes, (UTC)"
                                     'Example: "24.12.2023 23:56"',
                           time_zone='Example: "Europe/Berlin"',
                           announcement_channel='Channel into which announcement about this event will be posted.',
                           rating_required='Set a minimum rating required to reserve a nation.',
                           steam_required='Is steam verification required to reserve a nation?')
    async def add_hoi_game(self, interaction: discord.Interaction, date_time: str, time_zone: str, announcement_channel:
    discord.TextChannel, title: str, description: str, lobby_vc: discord.VoiceChannel,
                           global_database: bool = False, rating_required: int = 0, steam_required: bool = False):
        self.cursor, self.connection = config.setup()
        if interaction.user.guild_permissions.administrator:
            formats = ["%d.%m.%Y %H:%M", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"]
            for fmt in formats:
                try:
                    datetime_obj = datetime.datetime.strptime(date_time, fmt)
                    break
                except ValueError:
                    pass
            else:
                await interaction.response.send_message("Invalid date/time format",
                                                        ephemeral=True)
                return

            # Convert time_zone string to timezone object
            try:
                timezone_obj = pytz.timezone(time_zone)
            except pytz.UnknownTimeZoneError:
                await interaction.response.send_message("Invalid time zone.\nList of all valid timezones: "
                                                        "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                                                        ephemeral=True)
                return

            # Convert datetime_obj to UTC time
            datetime_obj = timezone_obj.localize(datetime_obj)
            datetime_obj_utc = datetime_obj.astimezone(pytz.utc)

            if not (0 <= rating_required <= 100):
                await interaction.channel.send("Please only enter values in this interval: <0;100>",
                                               ephemeral=True)

            embed = discord.Embed(
                title=f"**New event: {title}**",
                description=description,
                colour=discord.Colour.green()
            )
            message = await announcement_channel.send(embed=embed, view=presets.ReserveDialog(self.client))
            embed = discord.Embed(
                title=f"**New event: {title}**",
                description=description,
                colour=discord.Colour.green()
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.add_field(
                name="**Date & Time:**",
                value=f'<t:{int(datetime.datetime.timestamp(datetime_obj))}>',
                inline=False,
            )
            embed.add_field(
                name="Reserve a nation!",
                value='Click on the "Reserve" button to reserve a nation!',
                inline=True,
            )
            embed.add_field(
                name="Minimal rating:",
                value=f'{rating_required}%',
                inline=True,
            )
            embed.add_field(
                name="Steam verification required:",
                value=steam_required,
                inline=True,
            )
            embed.set_footer(text=f"Event ID:{message.id}")
            await message.edit(embed=embed)

            guild_event = await interaction.guild.create_scheduled_event(name=title, start_time=datetime_obj,
                                                                         description=description, channel=lobby_vc,
                                                                         entity_type=discord.EntityType.voice, privacy_level=discord.PrivacyLevel.guild_only)

            # Store datetime and timezone in MySQL database
            sql = "INSERT INTO events (guild_id, host_id, channel_id, event_start, rating_required, " \
                  "steam_required, message_id, global_database, title, description, voice_channel_id," \
                  "guild_event_id, timezone, created_at, updated_at) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
            values = (
                interaction.guild_id, interaction.user.id, announcement_channel.id,
                datetime_obj, rating_required / 100, steam_required,
                message.id, global_database, title, description, lobby_vc.id, guild_event.id, timezone_obj.zone)
            self.cursor.execute(sql, values)
            self.connection.commit()

            await interaction.response.send_message(f"Event added successfully!\nLobby URL for verified hosts: "
                                                    f"{config.ws_url}/dashboard/lobby/{interaction.guild.id}/{lobby_vc.id}\n"
                                                    f"If you want to apply join our communication server: "
                                                    f"{config.discord_invite_url}",
                                                    ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_hoi_game(client))
