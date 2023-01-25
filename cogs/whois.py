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
    async def whois(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        self.cursor.execute("SELECT * FROM players WHERE discord_id=%s" % member.id)
        player = self.cursor.fetchall()
        print(player)

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
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join([role.mention for role in roles]))
        embed.add_field(name="Main Role", value=member.top_role.mention)
        embed.add_field(name="Rating", value=f"{player[0][3]*100}%")
        embed.add_field(name="Steam Profile", value=f"https://steamcommunity.com/id/{player[0][1]}")
        await interaction.response.send_message(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(whois(client))
