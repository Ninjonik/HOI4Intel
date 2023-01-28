import datetime

import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime

import config
import presets
from presets import _add_player


class announce(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="announce")
    async def announce(self, interaction: discord.Interaction, message_content: str):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Working on it..., it may take a while", ephemeral=True)
            self.cursor.execute("SELECT ann_role FROM settings WHERE guild_id=%s" % interaction.guild.id)
            pre_role = self.cursor.fetchone()[0]
            role = discord.utils.get(interaction.guild.roles, id=pre_role)
            i = 0
            for member in interaction.guild.members:
                i += 1
                print(i)
                current_time = datetime.now()
                await _add_player(interaction.user.id, 1, current_time)
                self.cursor.execute("SELECT player_id FROM player_ann_blacklist WHERE player_id=%s" % member.id)
                blacklist = self.cursor.fetchone()
                if role in member.roles and blacklist is None:
                    try:
                        embed = discord.Embed(title=f"📢 {interaction.guild.name} Announcement!",
                                              description=f"By: {interaction.user}", color=0xff0000)
                        embed.add_field(name="Message:", value=message_content, inline=False)
                        embed.set_footer(text=f"You were DMed because you have a {role} role on server "
                                              f"{interaction.guild.name}. If you wish to unsubscribe to these DM announ"
                                              f"cements then you should remove the role by reacting on this message.")
                        channel = await member.create_dm()
                        message = await channel.send(embed=embed)
                        await message.add_reaction('🏷️')
                        print("Message sent!")

                    except Exception as e:
                        print(presets.prefix() + e)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(announce(client))
