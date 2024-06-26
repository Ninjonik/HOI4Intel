import random
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
import requests
import time
from typing import List, Dict


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


async def send_log_embed(guild: discord.Guild, user: discord.Member, title: str,
                         description: str, fields: List[Dict[str, str]], additional: List[Dict[str, str]],
                         color: discord.Color = discord.Color.blurple()):
    if user.id == client.user.id: return

    channel_id = 837333310140579861  # TODO: hardcoded for now
    channel = client.get_channel(channel_id)

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_author(name=user.name, icon_url=user.avatar)
    embed.set_thumbnail(url=guild.icon.url)

    # Add the fields
    for field in fields:
        embed.add_field(name=field["title"], value=field["description"], inline=False)

    # Add the additional fields
    result = "```js\n"
    result += f"User = {str(user.id)} \n"
    for field in additional:
        result += f"{field['title']} = {field['description']} \n"
    result += "```"
    embed.add_field(name="Additional information", value=result, inline=False)

    embed.set_footer(text=f"HOI4Intel Logging | {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    await channel.send(embed=embed)


async def on_start(server_name, server_description, guild_id, guild_count):
    # Establish database connection
    local_cursor, local_connection = config.setup()
    local_cursor.execute("SELECT guild_id FROM settings WHERE guild_id=%s", (guild_id,))
    settings = local_cursor.fetchall()
    current_time = datetime.datetime.now()
    current_date = datetime.datetime.now().date()
    if settings:
        local_cursor.execute(
            "SELECT updated_at FROM statistics WHERE guild_id=%s ORDER BY id DESC LIMIT 1", (guild_id,))
        row = local_cursor.fetchall()
        # Extract the date from the datetime object stored in the database
        db_datetime = row[0][0]
        db_date = db_datetime.date()
        # print(f" {presets.prefix()} Current date is: {current_date} meanwhile DB date is: {db_date}")
        if current_date != db_date:
            print(f"{presets.prefix()} Date is different, updating statistics for {server_name}")
            local_cursor.execute("UPDATE settings SET guild_name=%s, guild_desc=%s, updated_at=%s"
                                 " WHERE guild_id=%s", (server_name, server_description,
                                                        current_time, guild_id))
            local_cursor.execute(
                "INSERT INTO statistics (guild_id, created_at, updated_at, count) VALUES (%s, %s, %s, %s) ", (
                    guild_id, current_time, current_time, guild_count))
            local_connection.commit()
    local_connection.close()


@tasks.loop(hours=24)
async def update_guild_data(guilds):
    for guild in guilds:
        # print(f"{presets.prefix()} Initializing guild {guild.name}")
        await on_start(guild.name, guild.description, guild.id, guild.member_count)
        # print(f"{presets.prefix()} Guild {guild.name} initialized!")


async def guilds_redis_sync():
    cursor, connection = config.dictionary_setup()
    cursor.execute(f'SELECT * FROM settings ORDER BY updated_at DESC LIMIT {len(client.guilds)}')
    guilds = cursor.fetchall()

    print(presets.prefix() + " Syncing Redis database....")

    for guild in guilds:
        r = config.redis_connect()
        mapping = {
            'guild_id': guild["guild_id"],
            'guild_name': guild["guild_name"],
            'guild_desc': guild["guild_desc"],
            'wuilting_channel_id': guild["wuilting_channel_id"],
            'log_channel': guild["log_channel"],
            'custom_channel': guild["custom_channel"],
            'custom_channel_2': guild["custom_channel_2"],
            'verify_role': guild["verify_role"],
            'tts': guild["tts"],
            'automod': guild["automod"],
            'minimal_age': guild["minimal_age"],
            'steam_verification': guild["steam_verification"],
        }
        converted_mapping = {}
        for k, v in mapping.items():
            converted_mapping[k] = v if v is not None else ''
        r.hset(f'guild:{str(guild["guild_id"])}', mapping=converted_mapping, )


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
                                                           name=f"{memberCount} people! 😀"))
    await asyncio.sleep(10)

    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Activity(type=discord.ActivityType.competing,
                                                           name=f"Winning in '41 🎖️"))
    await asyncio.sleep(10)


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('*'), intents=discord.Intents().all())
        self.cursor, self.connection = config.setup()
        self.cogsList = ["cogs.calculate", "cogs.whois", "cogs.dice", "cogs.randomcog", "cogs.guessgame", "cogs.advent",
                         "cogs.clear", "cogs.setup", "cogs.add_record", "cogs.verify", "cogs.announce",
                         "cogs.setup_custom_channels", "cogs.test", "cogs.add_hoi_game", "cogs.add_blog", "cogs.guides",
                         "cogs.start_hoi_game", "cogs.add_player_list", "cogs.end_hoi_game", "cogs.request_steam",
                         "cogs.help", "cogs.ban", "cogs.unban", "cogs.server", "cogs.gamble",
                         "cogs.crash", "cogs.clearplayerlist", "cogs.clearreservations", "cogs.end_wuilting"]

    @tasks.loop(seconds=1400)
    async def refreshConnection(self):
        print(presets.prefix() + " Refreshing DB Connection")
        self.cursor, self.connection = config.setup()
        if self.connection.is_connected():
            db_Info = self.connection.get_server_info()
            print(presets.prefix() + " Connected to MySQL Server version ", db_Info)

    async def check_toxicity(self, message):
        self.cursor, self.connection = config.setup()
        toxicityValue = 0
        if message.author != client.user and message.content:
            message.content = (message.content[:75] + '..') if len(message.content) > 75 else message.content
            member = message.author
            analyze_request = {
                'comment': {'text': message.content},
                'requestedAttributes': {'TOXICITY': {}}
            }

            query = "INSERT INTO wwcbot_filter_logs (guildId, created_at, updated_at, message, authorId, result) " \
                    "VALUES (%s, NOW(), NOW(), %s, %s, %s)"
            values = (
                message.guild.id, message.content, message.author.id, toxicityValue)
            self.cursor.execute(query, values)
            self.cursor.execute('SELECT log_channel FROM settings WHERE guild_id=%s', (message.guild.id,))
            r = config.redis_connect()
            automod = r.hget(f'guild:{str(message.guild.id)}', 'automod')
            if not automod or automod == '0' or automod == 0:
                return False
            log_channel = self.cursor.fetchone()
            if log_channel and log_channel[0]:
                log_channel = log_channel[0]
                log_channel = message.guild.get_channel(log_channel)
            else:
                return False

            try:
                response = presets.perspective.comments().analyze(body=analyze_request).execute()
                toxicityValue = (response["attributeScores"]["TOXICITY"]["summaryScore"]["value"])

                if toxicityValue >= 0.70:
                    await message.delete()
                    if toxicityValue < 0.75:
                        punishment = "Original message has been deleted."
                    elif 0.75 <= toxicityValue < 0.85:
                        punishment = "Original message has been deleted. You have been timed-outed for 5 minutes."
                        timeMessage = datetime.datetime.now().astimezone() + datetime.timedelta(minutes=5)
                        await member.timeout(timeMessage, reason=f"Inappropriate message with value {toxicityValue}")
                    elif 0.85 <= toxicityValue < 0.90:
                        punishment = "Original message has been deleted. You have been timed-outed for 15 minutes."
                        timeMessage = datetime.datetime.now().astimezone() + datetime.timedelta(minutes=15)
                        await member.timeout(timeMessage, reason=f"Inappropriate message with value {toxicityValue}")
                    else:
                        punishment = "Original message has been deleted. You have been kicked from the server. Please" \
                                     " refrain from such a toxicity if you dont want to face harsher consequences."
                        await member.kick(reason=f"Inappropriate message with value {toxicityValue}")

                    channel = await member.create_dm()
                    embed = discord.Embed(title="You have been auto-moderated",
                                          description="One of your messages has been flagged as inappropriate which has"
                                                      " resulted in the following punishment(s):",
                                          color=0xe01b24)
                    embed.set_author(name="HOI4Intel")
                    embed.add_field(name="Message Content:", value=message.content, inline=False)
                    embed.set_footer(text="If you feel that this punishment is a mistake / inappropriate then"
                                          " please contact HOI4Intel Staff.")
                    embed.add_field(name="Punishment:", value=punishment, inline=False)
                    await channel.send(embed=embed)
                    embed.add_field(name="Time", value=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                                    inline=True)
                    embed.add_field(name="User:", value=member, inline=False)
                    embed.add_field(name="Toxicity Value:", value=toxicityValue)
                    embed.set_footer(text="This message was sent to the user. Consider "
                                          "taking more actions if needed.")
                    await log_channel.send(embed=embed)

                    query = "INSERT INTO wwcbot_filter_logs (guildId, created_at, updated_at, message, authorId, result) " \
                            "VALUES (%s, NOW(), NOW(), %s, %s, %s)"
                    values = (
                        message.guild.id, message.content, message.author.id, toxicityValue)
                    self.cursor.execute(query, values)
                    self.connection.commit()
                    return True

            except Exception as e:
                # embed = discord.Embed(title="Auto-Moderation Error",
                #                       description="HOI4Intel has been unable to moderate this message.",
                #                       color=0xff8000)
                # embed.add_field(name="Error", value=e, inline=False)
                # embed.add_field(name="Message", value=message.content, inline=True)
                # embed.add_field(name="Time", value=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), inline=True)
                # embed.set_author(name="HOI4Intel")
                # embed.add_field(name="User:", value=member, inline=True)
                # embed.add_field(name="Value of toxicity:", value=toxicityValue, inline=True)
                # await log_channel.send(embed=embed)
                pass

        if message.author != client.user and message.attachments and not message.author.bot:
            member = message.author
            self.cursor.execute('SELECT log_channel FROM settings WHERE guild_id=%s', (message.guild.id,))
            log_channel = self.cursor.fetchone()
            if log_channel and log_channel[0]:
                log_channel = log_channel[0]
                log_channel = message.guild.get_channel(log_channel)
            else:
                return False
            for attachment in message.attachments:
                url = (f'https://api.moderatecontent.com/moderate/?key={config.moderate_content_api_key}'
                       f'&url={attachment.url}')
                resp = requests.get(url=url)
                data = resp.json()
                if data["rating_letter"] == "a" or data["rating_letter"] == "t" or data["predictions"]["adult"] > 30:
                    await message.delete()
                    try:
                        punishment = "Original message has been deleted. You have been timed-outed for 15 seconds."
                        timeMessage = datetime.datetime.now().astimezone() + datetime.timedelta(seconds=15)
                        await member.timeout(timeMessage, reason=f"Inappropriate image attachment")

                        channel = await member.create_dm()
                        embed = discord.Embed(title="You have been auto-moderated",
                                              description="One of your messages has been flagged as inappropriate "
                                                          "which has"
                                                          " resulted in the following punishment(s):",
                                              color=0xe01b24)
                        embed.set_author(name="HOI4Intel")
                        embed.add_field(name="Image URL:", value=attachment.url, inline=False)
                        embed.set_footer(text="If you feel that this punishment is a mistake / inappropriate then"
                                              " please contact HOI4Intel Staff.")
                        embed.add_field(name="Punishment:", value=punishment, inline=False)

                        await channel.send(embed=embed)
                        embed.add_field(name="Values", value=f"Rating: {data['rating_letter']},\n"
                                                             f"Adult predictions: {data['predictions']['adult']}")
                        embed.add_field(name="Time", value=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                                        inline=True)
                        embed.add_field(name="User:", value=member, inline=False)
                        embed.set_footer(text="This message was sent to the user. Consider "
                                              "taking more actions if needed.")
                        await log_channel.send(embed=embed)
                        return True
                        break
                    except Exception as e:
                        embed = discord.Embed(title="Auto-Moderation Error",
                                              description="HOI4Intel has been unable to moderate this image.",
                                              color=0xff8000)
                        embed.add_field(name="Error", value=e, inline=False)
                        embed.add_field(name="Image URL", value=attachment.url, inline=True)
                        embed.add_field(name="Time", value=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                                        inline=True)
                        embed.set_author(name="HOI4Intel")
                        embed.add_field(name="User:", value=member, inline=True)
                        await log_channel.send(embed=embed)
                        break
            return False

        return False

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
        await guilds_redis_sync()
        print(presets.prefix() + " Initializing status....")
        if not statusLoop.is_running():
            statusLoop.start()
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

    async def on_message(self, message):
        if await self.check_toxicity(message):
            return

        try:
            # Add randomly generated money for each message based off length
            bonus = len(message.content) * random.randint(1, 10)
            self.cursor.execute("UPDATE players SET currency = currency + %s WHERE discord_id=%s",
                                (bonus, message.author.id,))
            self.connection.commit()
        except Exception as e:
            print(e)

        # Wuilting

        guild = message.guild
        if guild:
            r = config.redis_connect()
            wuilting_channel_id = r.hget(f'guild:{str(guild.id)}', 'wuilting_channel_id')
            if wuilting_channel_id and message.channel.id == int(wuilting_channel_id):
                wuilting_channel = message.guild.get_channel(int(wuilting_channel_id))
                channel_history = [message async for message in wuilting_channel.history(limit=6)]
                if len(channel_history) <= 1 and not message.author.bot:
                    embed = discord.Embed(
                        title="🌟 Welcome to the Wuilting! 🚀",
                        description="Embark on a linguistic journey with a twist! 📜✨",
                        color=0x3498db
                    )

                    embed.add_field(
                        name="**How to Play:**",
                        value="React with your enthusiasm to join this linguistic adventure! 🎉",
                        inline=False
                    )

                    embed.add_field(
                        name="**Rules:**",
                        value="1️⃣ Only your 1. word in a message counts, others are ignored. 🤞\n"
                              "2️⃣ You can only type if someone else has written before you. 🤔\n"
                              "3️⃣ If you want to end a sentence, simply put a dot after the last word, e.g., "
                              "'afternoon.' - same goes for commas, 'afternoon,' - "
                              "there is no need for spaces as the program adds them after each word. 📅\n"
                              "5️⃣ After a day, all words will be compiled into a text. 🔄\n"
                              "6️⃣ After a month, witness **the book** as the text transforms! 🔄",
                        inline=False
                    )

                    embed.add_field(
                        name="**Quick Reminder:**",
                        value="The last 5 words are what everyone sees! 🕵️‍♂️",
                        inline=False
                    )

                    embed.add_field(
                        name="**Are you ready to shape our collective story?**",
                        value="🌱✨",
                        inline=False
                    )

                    embed.set_thumbnail(url=guild.icon)

                    await wuilting_channel.send(embed=embed)
                    await message.delete()
                    return
                elif len(channel_history) > 5:
                    if not channel_history[5].author.bot:
                        await channel_history[5].delete()
                elif channel_history[1].author == message.author:
                    await message.delete()
                    return

                if not message.author.bot:
                    message_text = message.content.split(' ')[0]
                    r.rpush(f"guild:{str(guild.id)}:wuilting", message_text)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if (before.content == "" and after.content == "") or (before.content == after.content): return
        await send_log_embed(
            after.guild,
            before.author,
            "Message edited",
            f"Message has been edited in {after.channel.mention}",
            [
                {
                    "title": "Previous message",
                    "description": before.content
                },
                {
                    "title": "Current message",
                    "description": after.content
                }
            ],
            [
                {
                    "title": "Message",
                    "description": str(after.id)
                }
            ],
            discord.Color.blue()
        )
        await self.check_toxicity(after)

    async def on_message_delete(self, message: discord.Message) -> None:
        await send_log_embed(
            message.guild,
            message.author,
            "Message removed",
            f"Message was removed in {message.channel.mention}",
            [
                {
                    "title": "Message Content",
                    "description": message.content
                }
            ],
            [
                {
                    "title": "Message",
                    "description": str(message.id)
                }
            ],
            discord.Color.red()
        )

    async def on_guild_remove(self, guild):
        pass

    async def on_guild_join(self, guild):
        general = await guild.create_text_channel("📢hoi4intel-bot-info")
        await general.edit(position=0)

        if general and general.permissions_for(guild.me).send_messages:
            embed = discord.Embed(title="How to setup the bot?",
                                  description="To setup the bot you need to run the following commands",
                                  color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url=client.user.avatar)
            embed.add_field(name="1.) /setup",
                            value="Using this command you setup the basic server information so that the bot can "
                                  "function properly.",
                            inline=False)
            embed.add_field(name="2.) /setup_custom_channels (Optional)",
                            value="Using this command you can set up voice channels for a) "
                                  "creating custom temporary channels and b) creating custom permanent channels.",
                            inline=False)
            embed.add_field(name="Need help with anything?",
                            value="Check out our wiki: https://hoi.igportals.eu/wiki\n"
                                  "Setup guide: https://hoi.igportals.eu/wiki/article/9/how-to-setup-the-bot",
                            inline=False)
            embed.set_footer(
                text=f"If you have any questions regarding the bot you can always seek help at HOI4Intel's Discord by "
                     f"contacting the Staff Team.\n"
                     f"Discord: {config.discord_invite_url}")
            await general.send("You may delete this channel now.", embed=embed)

        try:
            cursor.execute(
                "INSERT INTO settings (created_at, updated_at, guild_name, "
                "guild_id) VALUES (NOW(), NOW(), %s, %s)",
                "ON DUPLICATE KEY UPDATE guild_name = %s, updated_at = NOW()",
                ((guild.name, guild.id, guild.name)))
            connection.commit()
        except Exception as e:
            print(e)

    async def on_voice_state_update(self, member, before, after):
        await self.refreshConnection()

        if after.channel:
            channel = after.channel
        else:
            channel = before.channel
        guild = channel.guild

        # LOBBY

        # Joining

        if guild.voice_client:
            if guild.voice_client.is_connected() and after.channel:
                # print(f"{member} has joined {channel.name}")
                await self.send_join_request(member, channel.id)
                return

            # Leaving
            if guild.voice_client.is_connected() and before.channel:
                # print(f"{member} has left {channel.name}")
                await self.send_leave_request(member, channel.id)
                return

        # END OF LOBBY

        # CUSTOM CHANNELS

        if before.channel is not None and before.channel.name.endswith(member.display_name) \
                and before.channel.name.startswith("TC"):
            await before.channel.delete(reason="Owner left the channel.")
            return

        if after.channel is not None:
            self.cursor.execute("SELECT custom_channel, custom_channel_2 FROM settings "
                                "WHERE guild_id=%s" % channel.guild.id)
            db_custom_channel = self.cursor.fetchone()

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

            if db_custom_channel and channel.id == db_custom_channel[0]:
                custom_channel = await guild.create_voice_channel(f"TC | {member.display_name}",
                                                                  category=channel.category)
                await custom_channel.set_permissions(member, overwrite=overwrite,
                                                     reason="Owner of Custom Channel.")
                await member.move_to(custom_channel)
            elif db_custom_channel and channel.id == db_custom_channel[1]:
                for voice_channel in guild.voice_channels:
                    if voice_channel.name.startswith("PC") and voice_channel.name.endswith(member.display_name):
                        await voice_channel.delete()
                custom_channel = await guild.create_voice_channel(f"PC | {member.display_name}",
                                                                  category=channel.category)
                await custom_channel.set_permissions(member, overwrite=overwrite,
                                                     reason="Owner of Custom Channel.")
                await member.move_to(custom_channel)
            return

        # END OF CUSTOM CHANNELS

    async def send_join_request(self, player, lobby_id):
        url = f"{config.ws_url}/lobby/send"
        rating = await presets._add_player_name(player.id, player.name, 0.5)
        payload = {
            "user": {
                "discord_id": f"{player.id}",
                "discord_name": player.name,
                "rating": rating,
                "country": player.display_name,
                "joined": time.time()
            },
            "action": {
                "none": "none"
            },
            "lobby_id": f"{lobby_id}",
            "token": config.comms_token
        }
        response = await presets.send_http_request(url, payload)

    async def send_leave_request(self, player, lobby_id):
        url = f"{config.ws_url}/lobby/send"
        payload = {
            "user": {
                "discord_id": f"{player.id}"
            },
            "action": "delete",
            "lobby_id": f"{lobby_id}",
            "token": config.comms_token
        }
        response = await presets.send_http_request(url, payload)

    async def on_member_join(self, member: discord.Member):

        await send_log_embed(
            member.guild,
            member,
            "Member joined",
            f"A new user {member.mention} has joined",
            [
                {
                    "title": "Account Age",
                    "description": f"<t:{int(round(member.created_at.timestamp()))}:F> - "
                                   f"<t:{int(round(member.created_at.timestamp()))}:R>"
                },
                {
                    "title": "New member count",
                    "description": member.guild.member_count
                }
            ],
            [],
            discord.Color.green()
        )

        self.cursor, self.connection = config.setup()
        self.cursor.execute("SELECT minimal_age FROM settings WHERE guild_id=%s", (member.guild.id,))
        minimal_age = self.cursor.fetchone()[0]

        current_time_utc = datetime.datetime.now(datetime.timezone.utc)
        account_age_days = (current_time_utc - member.created_at).days

        if account_age_days < minimal_age:
            try:
                embed = discord.Embed(title=f"HOI4Intel Warning",
                                      url="https://hoi.igportals.eu/", description=(f"{member.guild.name} is "
                                                                                    f"protected by HOI4Intel's account "
                                                                                    f"age check."),
                                      color=0xff0000)
                embed.set_thumbnail(url=member.guild.icon)
                embed.add_field(name="Account not old enough!",
                                value=f"Hello there,\nthis server requires your account to be at least {minimal_age} "
                                      f"days old.\nUnfortunately your current account age is only {account_age_days} "
                                      f"days which makes you not eligible for joining this server.\nMake sure to reach "
                                      f"out to server admins if you think this is a mistake.",
                                inline=True)
                channel = await member.create_dm()
                await channel.send(embed=embed)
            except Exception as e:
                print(e)
            await member.kick(reason=f"Account not old enough. Account age: {account_age_days} days.")

        self.cursor, self.connection = config.setup()
        self.cursor.execute("SELECT voice_channel_id, started, title, host_id FROM events "
                            "WHERE guild_id=%s ORDER BY id DESC LIMIT 1", (member.guild.id,))
        data = self.cursor.fetchone()
        channel_id, started, title, host_id = data
        if started == 1:
            embed = discord.Embed(
                title=f"📢 {title} HOI4 Game is currently in here!",
                description=f"Hosted by: {member.guild.get_member(host_id)}",
                color=0x00ff00
            )
            embed.add_field(
                name="Lobby VC:",
                value=member.guild.get_channel(channel_id).mention,
                inline=False
            )
            embed.set_footer(
                text="🤖 This is an automatic message, please do not reply to it."
            )
            try:
                channel = await member.create_dm()
                await channel.send(embed=embed)
            except Exception as e:
                print(e)
                channel = member.guild.system_channel
                await channel.send(member.mention, embed=embed)

    async def on_member_remove(self, member: discord.Member):
        await send_log_embed(
            member.guild,
            member,
            "Member left",
            f"A user {member.mention} left",
            [
                {
                    "title": "Account Age",
                    "description": f"<t:{int(round(member.created_at.timestamp()))}:F> - "
                                   f"<t:{int(round(member.created_at.timestamp()))}:R>"
                },
                {
                    "title": "Time in server",
                    "description": f"<t:{int(round(member.joined_at.timestamp()))}:F> - "
                                   f"<t:{int(round(member.joined_at.timestamp()))}:R>"
                },
                {
                    "title": "New member count",
                    "description": member.guild.member_count
                }
            ],
            [],
            discord.Color.red()
        )

    async def on_member_ban(self, member: discord.Member):
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            await send_log_embed(
                member.guild,
                member,
                "Member has been banned",
                f"User {member.mention} has been banned by {entry.user.mention}",
                [
                    {
                        "title": "Account Age",
                        "description": f"<t:{int(round(member.created_at.timestamp()))}:F> - "
                                       f"<t:{int(round(member.created_at.timestamp()))}:R>"
                    },
                    {
                        "title": "Time in server",
                        "description": f"<t:{int(round(member.joined_at.timestamp()))}:F> - "
                                       f"<t:{int(round(member.joined_at.timestamp()))}:R>"
                    },
                    {
                        "title": "Reason",
                        "description": f"{entry.reason}"
                    },
                    {
                        "title": "New member count",
                        "description": member.guild.member_count
                    }
                ],
                [
                    {
                        "title": "Banner",
                        "description": entry.user.id
                    }
                ],
                discord.Color.dark_red()
            )

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.name == after.name: return
        await send_log_embed(
            after.guild,
            after,
            "Member update",
            "The member has updated their profile",
            [],
            [
                {
                    "title": "Previous Profile",
                    "description": f"Nickname: {before.nick}"
                                   f"Roles: {', '.join(role.name for role in before.roles)}"
                },
                {
                    "title": "New Profile",
                    "description": f"Nickname: {after.nick}"
                                   f"Roles: {', '.join(role.name for role in after.roles)}"
                }
            ],
            discord.Color.teal()
        )


client = Client()
client.run(presets.token)
