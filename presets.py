import discord
import discord.utils
from colorama import Back, Fore, Style
from datetime import datetime
import os
import random
import datetime
import string
import config
from PIL import Image, ImageDraw, ImageFont
from googleapiclient import discovery
from slugify import slugify
import aiohttp


def prefix():
    return (Back.BLACK + Fore.GREEN + datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + Back.RESET + Fore.WHITE +
            Style.BRIGHT)


token = config.bot_token

admins = {
    "Ninjonik#6793",
    "Nullingo#5266",
    "DragonMan#1262",
    "no idea#8824"
}

perspective = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=config.API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)

time_formats = [
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y/%m/%d %H:%M:%S.%f',
    '%Y/%m/%d %H:%M:%S',
    '%Y/%m/%d %H:%M',
    '%Y.%m.%d %H:%M:%S.%f',
    '%Y.%m.%d %H:%M:%S',
    '%Y.%m.%d %H:%M',
    '%Y,%m,%d %H:%M:%S.%f',
    '%Y,%m,%d %H:%M:%S',
    '%Y,%m,%d %H:%M',
    '%d.%m.%Y %H:%M:%S.%f',
    '%d.%m.%Y %H:%M:%S',
    '%d.%m.%Y %H:%M',
    '%d/%m/%Y %H:%M:%S.%f',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%m/%d/%Y %H:%M:%S.%f',
    '%m/%d/%Y %H:%M:%S',
    '%m/%d/%Y %H:%M',
    '%d-%m-%Y %H:%M:%S.%f',
    '%d-%m-%Y %H:%M:%S',
    '%d-%m-%Y %H:%M',
    '%m-%d-%Y %H:%M:%S.%f',
    '%m-%d-%Y %H:%M:%S',
    '%m-%d-%Y %H:%M',
    '%d.%m.%y %H:%M:%S.%f',
    '%d.%m.%y %H:%M:%S',
    '%d.%m.%y %H:%M',
    '%d/%m/%y %H:%M:%S.%f',
    '%d/%m/%y %H:%M:%S',
    '%d/%m/%y %H:%M',
    '%m/%d/%y %H:%M:%S.%f',
    '%m/%d/%y %H:%M:%S',
    '%m/%d/%y %H:%M',
]


async def send_http_request(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.text()


async def ban(member, reason):
    await member.ban(reason=reason)


async def kick(member):
    await member.kick()


def check_perm(member):
    if member in admins:
        return True
    else:
        return False


def check_host(user_id):
    cursor, connection = config.setup()
    cursor.execute("SELECT r.role_id FROM users AS u "
                   "INNER JOIN assigned_roles AS r ON u.id=r.entity_id "
                   "WHERE u.discord_id=%s", (user_id,))
    data = cursor.fetchone()
    print(data)
    if data and data[0] < 4:
        return True
    else:
        return False


def log(content):
    print(prefix() + content)


async def _add_player_name(player_id, player_name, rating_percentage):
    cursor, connection = config.setup()
    try:
        cursor.execute(
            "INSERT INTO players (discord_id, discord_name, rating, created_at, updated_at) "
            "VALUES (%s, %s, %s, NOW(), NOW()) "
            "ON DUPLICATE KEY UPDATE rating = %s, discord_name = %s, updated_at = NOW()",
            (player_id, player_name, rating_percentage, rating_percentage, player_name))
        connection.commit()
        cursor.execute(
            "INSERT INTO player_records (player_id, guild_id, host_id, rating, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, NOW(), NOW())",
            (player_id, 820918304176340992, 1063766598197981215, rating_percentage))
        # TODO: Hardcoded for now
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(e)


class UpdateRoles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="War Discussion Access", style=discord.ButtonStyle.success, custom_id="ur_war_discussion",
                       emoji="📜")
    async def war_discussion(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="War Discussion Access")
        if role in interaction.user.roles:
            await interaction.user.remove_roles(discord.utils.get(interaction.user.guild.roles,
                                                                  name="War Discussion Access"))
        else:
            await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles,
                                                               name="War Discussion Access"))

        msg = await interaction.response.send_message("Your roles have been updated.", ephemeral=True)

    @discord.ui.button(label="Military Games Access", style=discord.ButtonStyle.danger, custom_id="ur_military_games",
                       emoji="🎮")
    async def military_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Military Games Access")
        if role in interaction.user.roles:
            await interaction.user.remove_roles(discord.utils.get(interaction.user.guild.roles,
                                                                  name="Military Games Access"))
        else:
            await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles,
                                                               name="Military Games Access"))
        msg = await interaction.response.send_message("Your roles have been updated.", ephemeral=True)

    @discord.ui.button(label="Roblox Access", style=discord.ButtonStyle.secondary, custom_id="ur_roblox",
                       emoji="✨")
    async def roblox(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Roblox Access")
        if role in interaction.user.roles:
            await interaction.user.remove_roles(discord.utils.get(interaction.user.guild.roles,
                                                                  name="Roblox Access"))
        else:
            await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles,
                                                               name="Roblox Access"))

        msg = await interaction.response.send_message("Your roles have been updated.", ephemeral=True)

    @discord.ui.button(label="HOI4 Role", style=discord.ButtonStyle.primary, custom_id="ur_hoi4", emoji="🎖️")
    async def hoi4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles, name="HOI4 Access"))
        msg = await interaction.response.send_message("Your roles have been updated.", ephemeral=True)


class EntryDialog(discord.ui.View):
    def __init__(self, client):
        super().__init__(timeout=None)
        self.client = client

    if config.hoi:
        @discord.ui.button(label="HOI4 Role", style=discord.ButtonStyle.success, custom_id="ed_hoi4", emoji="🎖️")
        async def hoi4(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles, name="HOI4 Access"))
            msg = await interaction.response.send_message("Your roles have been updated.", ephemeral=True)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="ed_verify", emoji="✅")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Verified")
        if role not in interaction.user.roles:
            member = interaction.user
            await interaction.response.send_message("Generating image...")
            await interaction.channel.send("Please enter the following code: (you have 3 tries left)")

            if "Verified" not in [y.name.lower() for y in interaction.user.roles]:
                log(f" User {interaction.user.name} has started a verification process.")

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel

                characters = string.ascii_letters + string.digits
                key = ''.join(random.choice(characters) for i in range(8))

                filename = f'keys/{key}.png'
                text = key
                size = 180
                fnt = ImageFont.truetype('arial.ttf', size)
                # create image
                image = Image.new(mode="RGB", size=(int(size / 1.4) * len(text), size + 60), color="black")
                draw = ImageDraw.Draw(image)
                # draw text
                draw.text((10, 10), text, font=fnt, fill=(255, 255, 0), color="white")
                # save file
                image.save(filename)
                await interaction.channel.send(file=discord.File(filename))

                tries = 3

                while tries > 0:
                    user_key = await self.client.wait_for('message', check=check)
                    if user_key.content == key:
                        log(f" User {member.name}"
                            f"has successfully solved the captcha with {tries} tries left.")
                        embed = discord.Embed(
                            title=f"Customization - **Get  Roles**",
                            description="You've successfully completed the verification! "
                                        "**Now you'll be locked in a General section from which "
                                        "you can get out by simply chatting with others.** You can "
                                        "unlock additional channels immediately by clicking on one of the buttons below.",
                            colour=discord.Colour.blurple()
                        )
                        embed.set_thumbnail(url=interaction.guild.icon)
                        embed.add_field(
                            name='**War Discussion**',
                            value="If you came to the server to discuss various historical content or you have "
                                  "any questions about uniform/badge/... you've found -> it's the place for you.",
                            inline=False,
                        )
                        embed.add_field(
                            name="**Military Games**",
                            value='If you came to the server to take part in a discussion or came to find other people '
                                  'to play various Historical Games that took place in the 20th century, '
                                  "then it's the place for you!",
                            inline=True,
                        )
                        embed.add_field(
                            name="**Roblox Access**",
                            value='Click on this role if you want to stay updated on the brand new projects coming out '
                                  'of our Roblox game studio and participate in our Roblox-oriented channels!',
                            inline=True,
                        )
                        embed.set_footer(
                            text="Ahead of you is the last part of verification process - customization."
                        )

                        await interaction.channel.send(content=f"You have solved the verification, "
                                                               f"{interaction.user.mention}. "
                                                               f"Now please click on roles you want to get.",
                                                       embed=embed,
                                                       view=UpdateRoles())
                        await member.add_roles(discord.utils.get(member.guild.roles, name="Verified"))
                        os.remove(filename)
                        break
                    else:
                        tries = tries - 1
                        await interaction.channel.send(f"Incorrect, you have {tries} tries left.")
                        log(f" User {member.name} has failed captcha with "
                            f"{tries} left, generated key was {key} and they entered {user_key.content}")
                        continue
                if tries == 0:
                    os.remove(filename)
                    log(f" User {member.name} "
                        f"has been kicked from the server for not completing the captcha.")
                    await kick(member)


class test_modal(discord.ui.Modal, title='Questionnaire Response'):
    name = discord.ui.TextInput(label='Name')
    answer = discord.ui.TextInput(label='Answer', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction):
        await interaction.response.send_message('There was an error while processing the request.')


class ReserveNation(discord.ui.Modal, title='Reserve a nation!'):
    country = discord.ui.TextInput(label='Country Name')

    async def on_submit(self, interaction: discord.Interaction):

        self.cursor, self.connection = config.setup()

        country = self.country.value

        # Already Reserved Check

        self.cursor.execute("SELECT country FROM event_reservations WHERE player_id=%s AND event_message_id=%s"
                            % (interaction.user.id, interaction.message.id))
        exists = self.cursor.fetchone()

        if exists is not None:
            await interaction.response.send_message(f"You have already reserved {exists[0]} in this game!",
                                                    ephemeral=True)
            return

        # End

        # Country Already Reserved Check

        self.cursor.execute("SELECT country FROM event_reservations WHERE country='%s' AND event_message_id=%s"
                            % (country, interaction.message.id))
        reserved = self.cursor.fetchone()

        if reserved is not None:
            await interaction.response.send_message(f"{reserved[0]} is already reserved in this game!",
                                                    ephemeral=True)
            return

        # End

        # Enough Rating Check

        self.cursor.execute("SELECT profile_link, rating FROM players WHERE discord_id=%s" % interaction.user.id)
        profile_link = self.cursor.fetchone()

        self.cursor.execute("SELECT * FROM events WHERE message_id=%s" % interaction.message.id)
        event_data = self.cursor.fetchone()

        await _add_player_name(interaction.user.id, interaction.user.name, 0.5)

        # Already started check
        # TODO
        """
        if event_data:
            if event_data[15] == 1:
                await interaction.response.send_message("This event has already been started!")
                return
        """

        if event_data and event_data[9] == 0:
            self.cursor.execute(
                "SELECT SUM(rating) as SUM, COUNT(rating) AS CNT FROM player_records WHERE player_id=%s AND"
                " guild_id=%s" % (interaction.user.id, interaction.guild.id))
            total = self.cursor.fetchall()
            if total[0][0]:
                player_rating = total[0][0] / total[0][1]
            else:
                player_rating = 0.5
        else:
            player_rating = profile_link[1]

        if player_rating < event_data[7]:
            await interaction.response.send_message(f"You don't have enough rating to reserve for this game!",
                                                    ephemeral=True)
            return

        # End

        # Steam Verification Check

        if profile_link[0] is None and event_data[8] == 1:
            await interaction.response.send_message(f"You don't have steam verified which is required for this game.\n"
                                                    f"You can fix it here:"
                                                    f"https://hoi.theorganization.eu/steam/{interaction.user.id}",
                                                    ephemeral=True)
            return

        # End

        # Time Check

        if event_data[5] < datetime.datetime.now():
            await interaction.response.send_message(f"This event has already started, reservations are now closed.",
                                                    ephemeral=True)
            return

        # End

        # Insert into DB
        query = "INSERT INTO event_reservations (event_message_id, player_id, country, created_at, updated_at) VALUES " \
                "(%s, %s, %s, NOW(), NOW())"
        values = (interaction.message.id, interaction.user.id, country)
        self.cursor.execute(query, values)
        self.connection.commit()

        await interaction.response.send_message(f'You have reserved a {country} in the upcoming game.\n'
                                                f'Please note that Admins of {interaction.guild.name} '
                                                f'can remove your reservation if they decide to.\n'
                                                f'If you wish to remove your reservation, click on the '
                                                f'"Cancel Reservation" button.', ephemeral=True)

        # Create new embed

        embed = discord.Embed(
            title=f"**New event: {event_data[10]}**",
            description=event_data[11],
            colour=discord.Colour.green()
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(
            name="**Date & Time:**",
            value=f'<t:{int(datetime.datetime.timestamp(event_data[5]))}>',
            inline=False,
        )
        embed.add_field(
            name="Reserve a nation!",
            value='Click on the "Reserve" button to reserve a nation!',
            inline=True,
        )
        embed.add_field(
            name="Minimal rating:",
            value=f'{event_data[7] * 100}%',
            inline=True,
        )
        if event_data[8] == 1:
            steam_required = True
        else:
            steam_required = False
        embed.add_field(
            name="Steam verification required:",
            value=steam_required,
            inline=True,
        )

        # Get reserved players & nations list

        self.cursor.execute("SELECT country, player_id FROM event_reservations WHERE event_message_id=%s"
                            % interaction.message.id)
        reserved_all = self.cursor.fetchall()
        reserved_list = []
        for player in reserved_all:
            val = f"{interaction.guild.get_member(player[1]).mention} - {player[0]}"
            reserved_list.append(val)
        embed.add_field(
            name="Currently Reserved:",
            value="\n".join(reserved_list),
            inline=False,
        )
        embed.set_footer(text=f"Event ID:{interaction.message.id}")
        await interaction.message.edit(embed=embed)

    async def on_error(self, interaction: discord.Interaction):
        await interaction.response.send_message('There was an error while processing the request.', ephemeral=True)


class ReserveDialog(discord.ui.View):
    def __init__(self, client):
        super().__init__(timeout=None)
        self.cursor, self.connection = config.setup()

    @discord.ui.button(label="Reserve", style=discord.ButtonStyle.success, custom_id="rd_reserve", emoji="🔒")
    async def rd_reserve(self, interaction: discord.Interaction, button: discord.Button):
        self.cursor, self.connection = config.setup()
        await interaction.response.send_modal(ReserveNation())

    @discord.ui.button(label="Cancel Reservation", style=discord.ButtonStyle.danger, custom_id="rd_un_reserve",
                       emoji="🔓")
    async def rd_un_reserve(self, interaction: discord.Interaction, button: discord.Button):
        try:
            self.cursor, self.connection = config.setup()
            self.cursor.execute("DELETE FROM event_reservations WHERE event_message_id=%s AND player_id=%s",
                                (interaction.message.id, interaction.user.id))
            self.connection.commit()
        except Exception as e:
            await interaction.response.send_message("There has been an error while cancelling the reservation.",
                                                    ephemeral=True)
            print(prefix() + e)
            return

        # Create new embed

        self.cursor.execute("SELECT * FROM events WHERE message_id=%s" % interaction.message.id)
        event_data = self.cursor.fetchone()
        if event_data:
            embed = discord.Embed(
                title=f"**New event: {event_data[10]}**",
                description=event_data[11],
                colour=discord.Colour.green()
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.add_field(
                name="**Date & Time:**",
                value=f'<t:{int(datetime.datetime.timestamp(event_data[5]))}>',
                inline=False,
            )
            embed.add_field(
                name="Reserve a nation!",
                value='Click on the "Reserve" button to reserve a nation!',
                inline=True,
            )
            embed.add_field(
                name="Minimal rating:",
                value=f'{event_data[7] * 100}%',
                inline=True,
            )
            if event_data[8] == 1:
                steam_required = True
            else:
                steam_required = False
            embed.add_field(
                name="Steam verification required:",
                value=steam_required,
                inline=True,
            )

            # Get reserved players & nations list

            self.cursor.execute("SELECT country, player_id FROM event_reservations WHERE event_message_id=%s"
                                % interaction.message.id)
            reserved_all = self.cursor.fetchall()
            reserved_list = []
            for player in reserved_all:
                val = f"{interaction.guild.get_member(player[1]).mention} - {player[0]}"
                reserved_list.append(val)
            embed.add_field(
                name="Currently Reserved:",
                value="\n".join(reserved_list),
                inline=False,
            )
            embed.set_footer(text=f"Event ID:{interaction.message.id}")
            await interaction.message.edit(embed=embed)

            await interaction.response.send_message("You have successfully canceled the reservation.", ephemeral=True)


class Select(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(GuideMenu())


class GuideMenu(discord.ui.Select):
    def __init__(self):
        self.cursor, self.connection = config.dictionary_setup()
        self.cursor.execute("SELECT * FROM wiki_articles WHERE category_id=12")
        self.articles = self.cursor.fetchall()
        self.article_dict = {article['title']: article['id'] for article in self.articles}
        options = [discord.SelectOption(label=article['title'], emoji=article['emoji'])
                   for article in self.articles]

        super().__init__(placeholder="Please select the guide you want:", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_title = self.values[0]
        selected_id = self.article_dict[selected_title]
        slug_title = slugify(selected_title)
        link = f"https://hoi.theorganization.eu/wiki/article/{selected_id}/{slug_title}"

        await interaction.response.send_message(f"Guide for **{selected_title}** at: {link}", ephemeral=True)
