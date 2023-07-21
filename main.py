import threading

import discord
import discord.utils
from discord.ext import tasks, commands
from colorama import Fore
from datetime import datetime
import platform
import asyncio
import datetime
import config
import presets
import logging
import aiohttp
import openai
openai.api_key = config.openai_api_key
openai.api_base = config.openai_api_base
import time


def get_logger(name, filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(filename, mode='w')
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = get_logger('discord-bot', 'bot.log')


def custom_print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    logger.debug(message)
    __builtins__.print(*args, **kwargs)


# Replace the default print function with our custom print function
print = custom_print

intents = discord.Intents.all()
intents.typing = True
intents.presences = True
intents.members = True
intents.guilds = True

# Store the cursor object in a global variable
global cursor
global connection

user_cooldowns = {}

async def on_start(server_name, server_description, guild_id, guild_count):
    # Establish database connection
    local_cursor, local_connection = config.setup()
    local_cursor.execute("SELECT guild_id FROM settings WHERE guild_id='%s'" % guild_id)
    settings = local_cursor.fetchall()
    current_time = datetime.datetime.now()
    current_date = datetime.datetime.now().date()
    if settings:
        local_cursor.execute(
            "SELECT updated_at FROM statistics WHERE guild_id='%s' ORDER BY id DESC LIMIT 1" % guild_id)
        row = local_cursor.fetchall()
        # Extract the date from the datetime object stored in the database
        db_datetime = row[0][0]
        db_date = db_datetime.date()
        print(f" {presets.prefix()} Current date is: {current_date} meanwhile DB date is: {db_date}")
        if current_date != db_date:
            print(f"{presets.prefix()} Date is different, updating statistics for {server_name}")
            local_cursor.execute("UPDATE settings SET guild_name='%s', guild_desc='%s', updated_at='%s'"
                                 " WHERE guild_id='%s'" % (server_name, server_description,
                                                           current_time, guild_id))
            local_cursor.execute(
                "INSERT INTO statistics (guild_id, created_at, updated_at, count) VALUES (%s, '%s', '%s', %s) " % (
                    guild_id, current_time, current_time, guild_count))
            local_connection.commit()
    local_connection.close()


@tasks.loop(hours=24)
async def update_guild_data(guilds):
    for guild in guilds:
        print(f"{presets.prefix()} Initializing guild {guild.name}")
        await on_start(guild.name, guild.description, guild.id, guild.member_count)
        print(f"{presets.prefix()} Guild {guild.name} initialized!")


@tasks.loop(seconds=60)
async def guildLoop():
    # Establish database connection
    local_cursor, local_connection = config.setup()
    guildCount = len(client.guilds)
    local_cursor.execute("SELECT count(guild_id) as Counter FROM settings")
    dbCount = local_cursor.fetchone()
    if guildCount != int(dbCount[0]):
        print(presets.prefix() + " New guild was detected, restarting loop.")
        await update_guild_data(client.guilds)
    local_connection.close()


@tasks.loop(seconds=30)
async def statusLoop():
    await client.wait_until_ready()
    await client.change_presence(status=discord.Status.idle,
                                 activity=discord.Activity(type=discord.ActivityType.watching,
                                                           name=f"{len(client.guilds)} servers. 🧐"))
    await asyncio.sleep(10)
    memberCount = 0
    for guild in client.guilds:
        memberCount += guild.member_count
    await client.change_presence(status=discord.Status.dnd,
                                 activity=discord.Activity(type=discord.ActivityType.listening,
                                                           name=f"{memberCount} people! 😀", ))
    await asyncio.sleep(10)

    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Activity(type=discord.ActivityType.competing,
                                                           name=f"dsc.gg/wwc 🎖️",
                                                           url="https://discord.gg/dCVNQeywKY"))
    await asyncio.sleep(10)


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('*'), intents=discord.Intents().all())
        self.cursor, self.connection = config.setup()
        self.cogsList = ["cogs.calculate", "cogs.whois", "cogs.dice", "cogs.randomcog", "cogs.guessgame",
                         "cogs.clear", "cogs.setup", "cogs.add_record", "cogs.verify", "cogs.announce",
                         "cogs.setup_custom_channels", "cogs.test", "cogs.add_hoi_game", "cogs.add_blog", "cogs.guides",
                         "cogs.start_hoi_game", "cogs.add_player_list", "cogs.end_hoi_game", "cogs.request_steam",
                         "cogs.help", "cogs.ban", "cogs.unban", "cogs.server", "cogs.image"]

    @tasks.loop(seconds=1400)
    async def refreshConnection(self):
        print(presets.prefix() + " Refreshing DB Connection")
        self.cursor, self.connection = config.setup()
        if self.connection.is_connected():
            db_Info = self.connection.get_server_info()
            print(presets.prefix() + " Connected to MySQL Server version ", db_Info)

    async def setup_hook(self):
        for ext in self.cogsList:
            await self.load_extension(ext)

    async def on_ready(self):
        await self.refreshConnection()
        print(presets.prefix() + " Logged in as " + Fore.YELLOW + self.user.name)
        print(presets.prefix() + " Bot ID " + Fore.YELLOW + str(self.user.id))
        print(presets.prefix() + " Discord Version " + Fore.YELLOW + discord.__version__)
        print(presets.prefix() + " Python version " + Fore.YELLOW + platform.python_version())
        print(presets.prefix() + " Syncing slash commands....")
        synced = await self.tree.sync()
        print(presets.prefix() + " Slash commands synced " + Fore.YELLOW + str(len(synced)) + " Commands")
        print(presets.prefix() + " Running the web server....")
        print(presets.prefix() + " Initializing guilds....")
        print(presets.prefix() + " Initializing status....")
        if not statusLoop.is_running():
            statusLoop.start()
        if not guildLoop.is_running():
            guildLoop.start(),
        if not update_guild_data.is_running():
            update_guild_data.start(self.guilds)
        print(presets.prefix() + " Removing non-deleted Custom Channels.")
        for guild in self.guilds:
            for voice_channel in guild.voice_channels:
                if voice_channel.name.startswith("TC"):
                    await voice_channel.delete()

        # Inform guild admins that the bot has been restarted
        self.cursor.execute('SELECT log_channel FROM settings')
        guilds_db = self.cursor.fetchall()

        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction,
                                       error: discord.app_commands.AppCommandError) -> None:
            print(interaction)
            print(error)
            # Output: <discord.interactions.Interaction object at 0x000001EC1F1AD6C0>
            """
            if isinstance(error, discord.app_commands.errors.No):
                await interaction.response.send_message(
                    f'Command "{interaction.command.name}" is on cooldown, you can use it in '
                    f'{round(error.retry_after, 2)} seconds.',
                    ephemeral=True)
            """

    async def on_message(self, message):
        if client.user.mentioned_in(message):
            user_id = message.author.id

            # Check if the user has a cooldown record
            if user_id in user_cooldowns:
                last_message_time = user_cooldowns[user_id]
                current_time = time.time()

                # Check if the cooldown period (5 seconds) has passed
                if current_time - last_message_time < 5:
                    return  # Ignore the message as the cooldown hasn't expired yet

            # Update the user's last message timestamp to the current time
            user_cooldowns[user_id] = time.time()

            clear_message = message.content.replace(client.user.mention, '').strip()
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': clear_message},
                ]
            )
            await message.channel.send(response.choices[0].message.content)

    async def on_guild_join(self, guild):
        general = await guild.create_text_channel("📢hoi4intel-bot-info")
        await general.edit(position=0)
        if general and general.permissions_for(guild.me).send_messages:
            embed = discord.Embed(title="How to setup the bot?",
                                  description="To setup the bot you need to run the following commands",
                                  color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url=client.user.avatar.url)
            embed.add_field(name="1.) /setup",
                            value="Using this command you setup the basic server information so that the bot can "
                                  "function properly.",
                            inline=False)
            embed.add_field(name="2.) /setup_custom_channels (Optional)",
                            value="Using this command you can set up voice channels for a) "
                                  "creating custom temporary channels and b) creating custom permanent channels.",
                            inline=False)
            embed.add_field(name="Need help with anything?",
                            value="Check out our wiki: https://hoi.theorganization.eu/wiki\n"
                                  "Setup guide: https://hoi.theorganization.eu/wiki/article/9/how-to-setup-the-bot",
                            inline=False)
            embed.set_footer(
                text="If you have any questions regarding the bot you can always seek help at WWC's Discord by "
                     "contacting the Staff Team.\n"
                     "WWC's Discord: https://discord.gg/world-war-community-820918304176340992")
            await general.send("You may delete this channel now.", embed=embed)

    async def on_voice_state_update(self, member, before, after):
        await self.refreshConnection()

        if after.channel:
            channel = after.channel
        else:
            channel = before.channel
        guild = channel.guild

        # LOBBY

        # Joining

        print(guild.voice_client.is_connected())
        print(guild.voice_client)

        if guild.voice_client.is_connected() and after.channel:
            print(f"{member} has joined {channel.name}")
            await self.send_join_request(member, channel.id)

        # Leaving
        if guild.voice_client.is_connected() and before.channel:
            print(f"{member} has left {channel.name}")
            await self.send_leave_request(member, channel.id)

        # END OF LOBBY

        # CUSTOM CHANNELS

        if before.channel is not None and before.channel.name.endswith(member.display_name) \
                and before.channel.name.startswith("TC"):
            await before.channel.delete(reason="Owner left the channel.")

        if after.channel is not None:
            self.cursor.execute("SELECT custom_channel, custom_channel_2 FROM settings "
                                "WHERE guild_id='%s'" % channel.guild.id)
            db_custom_channel = self.cursor.fetchone()
            print(db_custom_channel)

            overwrite = discord.PermissionOverwrite()
            overwrite.manage_messages = True
            overwrite.manage_permissions = True
            overwrite.manage_events = True
            overwrite.manage_channels = True
            overwrite.read_message_history = True
            overwrite.mention_everyone = True
            overwrite.use_external_emojis = True
            overwrite.use_external_stickers = True
            overwrite.move_members = True
            overwrite.mute_members = True
            overwrite.use_voice_activation = True
            overwrite.use_embedded_activities = True
            overwrite.connect = True
            overwrite.speak = True

            if channel.id == db_custom_channel[0]:
                custom_channel = await guild.create_voice_channel(f"TC | {member.display_name}",
                                                                  category=channel.category)
                await custom_channel.set_permissions(member, overwrite=overwrite,
                                                     reason="Owner of Custom Channel.")
                await member.move_to(custom_channel)
            elif channel.id == db_custom_channel[1]:
                for voice_channel in guild.voice_channels:
                    if voice_channel.name.startswith("PC") and voice_channel.name.endswith(member.display_name):
                        await voice_channel.delete()
                custom_channel = await guild.create_voice_channel(f"PC | {member.display_name}",
                                                                  category=channel.category)
                await custom_channel.set_permissions(member, overwrite=overwrite,
                                                     reason="Owner of Custom Channel.")
                await member.move_to(custom_channel)

        # END OF CUSTOM CHANNELS

    async def send_join_request(self, player, lobby_id):
        url = "http://localhost:8000/lobby/send"
        payload = {
            "user": {
                "discord_id": f"{player.id}",
                "discord_name": player.name,
                "rating": 1,
                "country": player.display_name,
                "joined": 1689182629
            },
            "action": {
                "none": "none"
            },
            "lobby_id": f"{lobby_id}",
            "token": config.comms_token
        }
        response = await presets.send_http_request(url, payload)
        print("Join request response:", response)

    async def send_leave_request(self, player, lobby_id):
        url = "http://localhost:8000/lobby/send"
        payload = {
            "user": {
                "discord_id": f"{player.id}"
            },
            "action": "delete",
            "lobby_id": f"{lobby_id}",
            "token": config.comms_token
        }
        response = await presets.send_http_request(url, payload)
        print("Leave request response:", response)


client = Client()
client.run(presets.token)
