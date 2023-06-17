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

        roles = [role for role in member.roles]
        embed = discord.Embed(title="User info", description=f"{member.mention}'s information",
                              color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Name", value=f'{member.name}#{member.discriminator}')
        embed.add_field(name="Nickname", value=member.display_name)
        embed.add_field(name="Status", value=member.status)
        embed.add_field(name="Created At", value=member.created_at.strftime("%#d. %B %Y %H:%M:%S UTC "))
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%#d. %B %Y %H:%M:%S UTC "))
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join([role.mention for role in roles]), inline=False)
        embed.add_field(name="Main Role", value=member.top_role.mention, inline=False)

        self.cursor.execute("SELECT * FROM players WHERE discord_id=%s" % member.id)
        player = self.cursor.fetchall()

        query = "SELECT SUM(rating) as SUM, COUNT(rating) AS CNT FROM player_records WHERE player_id=%s "
        if host is not None:
            if global_records is True:
                query += "AND host_id=%s"
                values = (member.id, host.id)
                embed.add_field(name="Host", value=f"{host.name}#{host.discriminator}")
            else:
                query += "AND guild_id=%s AND host_id=%s"
                values = (member.id, interaction.guild.id, host.id)
                embed.add_field(name="Host", value=f"{host.name}#{host.discriminator}")
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
        total = self.cursor.fetchall()
        if total[0][0] is not None and total[0][1] is not None:
            rating = total[0][0] / total[0][1]
            embed.add_field(name="Rating", value=f"{rating * 100}%")
            embed.add_field(name="Steam Profile", value=player[0][4], inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Records for user with these parameters have not been found.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(whois(client))
