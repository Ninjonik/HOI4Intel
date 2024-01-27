import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config


class whois(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name='whois', description="Prints out basic information about the user.")
    async def whois(self, interaction: discord.Interaction, member: discord.Member = None, host: discord.Member = None,
                    global_records: bool = False):
        if member is None:
            member = interaction.user

        self.cursor, self.connection = config.setup()

        self.cursor.execute("SELECT * FROM players WHERE discord_id=%s" % member.id)
        player = self.cursor.fetchone()

        roles = [role for role in member.roles]
        embed = discord.Embed(title="User info", description=f"{member.name}'s information",
                              color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Name", value=f'{member.name}')
        embed.add_field(name="Nickname", value=member.display_name)
        embed.add_field(name="Money", value=player.currency)
        embed.add_field(name="Status", value=member.status)
        embed.add_field(name="Created At", value=member.created_at.strftime("%#d. %B %Y %H:%M:%S UTC "))
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%#d. %B %Y %H:%M:%S UTC "))
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join([role.mention for role in roles]), inline=False)
        embed.add_field(name="Main Role", value=member.top_role.mention, inline=False)

        query = "SELECT SUM(rating) as SUM, COUNT(rating) AS CNT FROM player_records WHERE player_id=%s "
        if host is not None:
            if global_records is True:
                query += "AND host_id=%s"
                values = (member.id, host.id)
                embed.add_field(name="Host", value=f"{host.name}")
            else:
                query += "AND guild_id=%s AND host_id=%s"
                values = (member.id, interaction.guild.id, host.id)
                embed.add_field(name="Host", value=f"{host.name}")
                embed.add_field(name="Server", value=interaction.guild.name)
        else:
            if global_records is False:
                query += "AND guild_id=%s"
                values = (member.id, interaction.guild.id)
                embed.add_field(name="Server", value=interaction.guild.name)
            else:
                values = member.id
                embed.add_field(name="Server", value=interaction.guild.name)

        self.cursor.execute(query % values)
        total = self.cursor.fetchone()
        if total[0] is not None and total[1] is not None:
            rating = total[0] / total[1]
            embed.add_field(name="Rating", value=f"{rating * 100}%")
            embed.add_field(name="Steam Profile", value=player[4], inline=False)

            # Retrieve last ratings
            query = "SELECT rating, host_id, guild_id, created_at, country FROM player_records WHERE player_id=%s " \
                    "ORDER BY id DESC LIMIT 10"
            self.cursor.execute(query, (member.id,))
            ratings = self.cursor.fetchall()
            table = f"Last 10 Ratings for {member.name}\n"
            table += "```\n"
            table += "{:<4} {:<9} {:<16} {:<16} {:<30} {:<20}\n".format("#", "Rating", "Country", "Host", "Server", "Date")
            for index, record in enumerate(ratings, start=1):
                rating_percent = "{:.2f}%".format(record[0] * 100)
                country = (str(record[4]) if record[4] is not None else "-").ljust(16)
                host_name = member.name.ljust(16)
                guild_name = (self.client.get_guild(record[2]).name[:30]).ljust(30)
                date = record[3].strftime("%Y-%m-%d %H:%M:%S UTC")
                table += "{:<4} {:<9} {:<16} {:<16} {:<30} {:<20}\n".format(index, rating_percent, country, host_name,
                                                                     guild_name, date)
            table += "```"
            table += "Complete list of ratings for this player available for hosts at: " \
                     "https://hoi.igportals.eu/players"

            await interaction.response.send_message(table, embed=embed)






        else:
            await interaction.response.send_message("Records for user with these parameters have not been found.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(whois(client))
