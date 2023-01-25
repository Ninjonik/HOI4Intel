import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config
import presets


class announce(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="announce")
    async def announce(self, interaction: discord.Interaction, message_content: str):
        self.cursor.execute("SELECT ann_role FROM settings WHERE guild_id=%s" % interaction.guild.id)
        pre_role = self.cursor.fetchone()[0]
        role = discord.utils.get(interaction.guild.roles, id=pre_role)
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Working on it..., it may take a while", ephemeral=True)
            for member in interaction.guild.members:
                if role in member.roles:
                    try:
                        embed=discord.Embed(title=f"📢 {interaction.guild.name} Announcement!",
                                            description=f"By: {interaction.user}", color=0xff0000)
                        embed.add_field(name="Message:", value=message_content, inline=False)
                        embed.set_footer(text=f"You were DMed because you have a {role} role on server "
                                              f"{interaction.guild.name}. If you wish to unsubscribe to these "
                                              f"DM announcements then you should remove the role.")
                        channel = await member.create_dm()
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(presets.prefix() + e)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(announce(client))
