import threading
from asyncio import tasks
from time import sleep

import discord
import discord.utils
from discord.ext import tasks, commands
from colorama import Back, Fore, Style
from datetime import datetime
import platform
import os
import random
import asyncio
import json
import datetime
import string
from pprint import pprint
import config
from PIL import Image, ImageDraw, ImageFont
import mysql.connector
import time
import presets
import git
import uuid

intents = discord.Intents.all()
intents.typing = True
intents.presences = True
intents.members = True
intents.guilds = True

# Store the cursor object in a global variable
global cursor
global connection

from http.server import HTTPServer, BaseHTTPRequestHandler


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'working')
        else:
            self.send_response(404)
            self.end_headers()


# Create an HTTP server
try:
    httpd = HTTPServer(('hoi.theorganization.eu', 8089), SimpleHTTPRequestHandler)
except:
    httpd = HTTPServer(('localhost', 8089), SimpleHTTPRequestHandler)

# Start the HTTP server in a separate thread
http_thread = threading.Thread(target=httpd.serve_forever)
http_thread.start()


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
                         "cogs.start_hoi_game", "cogs.add_player_list", "cogs.end_hoi_game", "cogs.request_steam"]

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
        print(presets.prefix() + " Syncing slash commands...")
        synced = await self.tree.sync()
        print(presets.prefix() + " Slash commands synced " + Fore.YELLOW + str(len(synced)) + " Commands")
        print(presets.prefix() + " Running the web server")
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
        if uuid.getnode() == 345048613385:
            for guild_db in guilds_db:
                if guild_db[0]:
                    channel = client.get_channel(guild_db[0])
                    repo = git.Repo(search_parent_directories=True)
                    checksum = repo.head.object.hexsha
                    await channel.send(f"The bot has been restarted. Any old interactions that have been created "
                                       f"before and "
                                       f"require buttons to work will not work anymore. We apologize for the "
                                       f"inconvenience."
                                       f"\nVersion checksum: {checksum}"
                                       f"\nIf you have any problems regarding the bot, seek support at: "
                                       f"https://discord.gg/world-war-community-820918304176340992"
                                       f"\nOr at our wiki: https://hoi.theorganization.eu/wiki")

    async def on_guild_join(self, guild):
        # TODO: This method might not be working
        general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
        if general and general.permissions_for(guild.me).send_messages:
            embed = discord.Embed(title="How to setup the bot?",
                                  description="To setup the bot you need to run the following commands",
                                  color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url=guild.icon_url)
            embed.add_field(name="2.) /setup_custom_channels",
                            value="Using this command you can set up voice channels for a) "
                                  "creating custom temporary channels and b) creating custom permanent channels.",
                            inline=False)
            embed.set_footer(
                text="If you have any questions regarding the bot you can always seek help at WWC's Discord by "
                     "contacting the Staff Team. WWC's Discord: "
                     "https://discord.gg/world-war-community-820918304176340992")
            await general.send(embed=embed)

    async def on_voice_state_update(self, member, before, after):

        if before.channel is not None and before.channel.name.endswith(member.display_name) \
                and before.channel.name.startswith("TC"):
            await before.channel.delete(reason="Owner left the channel.")

        if after.channel is not None:
            channel = after.channel
            guild = channel.guild

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


client = Client()
client.run(presets.token)
http_thread.join()