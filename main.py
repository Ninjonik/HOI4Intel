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
from presets import _add_player

intents = discord.Intents.all()
intents.typing = True
intents.presences = True
intents.members = True
intents.guilds = True

# Store the cursor object in a global variable
global cursor
global connection


async def on_start(server_name, server_description, guild_id, guild_count):
    # Establish database connection
    cursor, connection = config.setup()
    cursor.execute("SELECT guild_id FROM settings WHERE guild_id='%s'" % guild_id)
    settings = cursor.fetchall()
    current_time = datetime.datetime.now()
    current_date = datetime.datetime.now().date()
    if settings:
        cursor.execute("SELECT updated_at FROM statistics WHERE guild_id='%s' ORDER BY id DESC LIMIT 1" % guild_id)
        row = cursor.fetchall()
        # Extract the date from the datetime object stored in the database
        db_datetime = row[0][0]
        db_date = db_datetime.date()
        print(f" {presets.prefix()} Current date is: {current_date} meanwhile DB date is: {db_date}")
        if current_date != db_date:
            print(f"{presets.prefix()} Date is different, updating statistics for {server_name}")
            cursor.execute("UPDATE settings SET guild_name='%s', guild_desc='%s', updated_at='%s'"
                           " WHERE guild_id='%s'" % (server_name, server_description,
                                                     current_time, guild_id))
            cursor.execute(
                "INSERT INTO statistics (guild_id, created_at, updated_at, count) VALUES (%s, '%s', '%s', %s) " % (
                    guild_id, current_time, current_time, guild_count))
            connection.commit()


@tasks.loop(hours=24)
async def update_guild_data(guilds):
    for guild in guilds:
        print(f"{presets.prefix()} Initializing guild {guild.name}")
        await on_start(guild.name, guild.description, guild.id, guild.member_count)
        print(f"{presets.prefix()} Guild {guild.name} initialized!")


@tasks.loop(seconds=60)
async def guildLoop():
    # Establish database connection
    cursor, connection = config.setup()
    guildCount = len(client.guilds)
    cursor.execute("SELECT count(guild_id) as Counter FROM settings")
    dbCount = cursor.fetchone()
    if guildCount != int(dbCount[0]):
        print(presets.prefix() + " New guild was detected, restarting loop.")
        await update_guild_data(client.guilds)


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
        super().__init__(command_prefix=commands.when_mentioned_or('.'), intents=discord.Intents().all())
        self.cursor, self.connection = config.setup()
        self.cogsList = ["cogs.calculate", "cogs.whois", "cogs.dice", "cogs.randomcog", "cogs.guessgame",
                         "cogs.clear", "cogs.setup", "cogs.add_record", "cogs.add_steam", "cogs.setupann",
                         "cogs.announce", "cogs.assign_roles_to_all"]

    async def setup_hook(self):
        for ext in self.cogsList:
            await self.load_extension(ext)

    async def on_ready(self):
        if self.connection.is_connected():
            db_Info = self.connection.get_server_info()
            print(presets.prefix() + " Connected to MySQL Server version ", db_Info)
        print(presets.prefix() + " Logged in as " + Fore.YELLOW + self.user.name)
        print(presets.prefix() + " Bot ID " + Fore.YELLOW + str(self.user.id))
        print(presets.prefix() + " Discord Version " + Fore.YELLOW + discord.__version__)
        print(presets.prefix() + " Python version " + Fore.YELLOW + platform.python_version())
        print(presets.prefix() + " Syncing slash commands...")
        synced = await self.tree.sync()
        print(presets.prefix() + " Slash commands synced " + Fore.YELLOW + str(len(synced)) + " Commands")
        print(presets.prefix() + " Initializing guilds....")
        print(presets.prefix() + " Initializing status....")
        if not statusLoop.is_running():
            statusLoop.start()
        if not guildLoop.is_running():
            guildLoop.start(),
        if not update_guild_data.is_running():
            update_guild_data.start(self.guilds)

    async def on_raw_reaction_add(self, payload):
        current_time = datetime.datetime.now()
        await _add_player(payload.user_id, 0.5, current_time)
        member = await client.fetch_user(payload.user_id)
        if payload.emoji.name == "🏷️":
            try:
                self.cursor.execute("INSERT INTO player_ann_blacklist (player_id) VALUES (%s)" % payload.user_id)
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                raise e
            try:
                channel = await member.create_dm()
                embed = discord.Embed(title=f"Unsubscribed from HOI4Intel's Announcements")
                embed.set_footer(text=f"You have successfully unsubscribed from HOI4Intel's Announcements. "
                                      f"This includes announcements from all servers that are using HOI4Intel. "
                                      f"If you want to get subscribe again then click on the reaction:")
                message = await channel.send(embed=embed)
                await message.add_reaction("👌")
            except Exception as e:
                raise e

        elif payload.emoji.name == "👌":
            self.cursor.execute("DELETE FROM player_ann_blacklist WHERE player_id=%s" % payload.user_id)
            self.connection.commit()
            try:
                channel = await member.create_dm()
                embed = discord.Embed(title=f"Subscribed to HOI4Intel's Announcements")
                embed.set_footer(text=f"You have successfully subscribed to HOI4Intel's Announcements. "
                                      f"This includes announcements from all servers that are using HOI4Intel. ")
                await channel.send(embed=embed)
            except Exception as e:
                raise e


client = Client()

client.run(presets.token)
