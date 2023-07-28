import json

import discord
from discord.ext import commands
from discord import app_commands

import config
import presets


class announce(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.dictionary_setup()

    @app_commands.command(name="announce")
    async def announce(self, interaction: discord.Interaction, message_content: str, event_id: str,
                       recipient: discord.User = None):
        self.cursor, self.connection = config.dictionary_setup()
        if interaction.user.guild_permissions.administrator:
            try:
                event_id = int(event_id)
            except ValueError:
                await interaction.response.send_message("🔟 Invalid event ID format. Please provide a valid ID.",
                                                        ephemeral=True)
                return
            await interaction.response.send_message("👷 Working on it..., it may take a while")
            if recipient is None:
                self.cursor.execute("SELECT countries, started FROM events WHERE message_id=%s", (event_id,))
                data = self.cursor.fetchone()
                voice_client = interaction.guild.voice_client
                await presets.playTTS(message_content, voice_client)
                if data and data["started"] != 2 and data["countries"]:
                    countries = json.loads(data["countries"])
                    for member, country in countries.items():
                        member = interaction.guild.get_member(int(member))
                        try:
                            embed = discord.Embed(title=f"📢 {interaction.guild.name} Announcement!",
                                                  description=f"By: {interaction.user}", color=0xff0000)
                            embed.add_field(name="Message:", value=message_content, inline=False)
                            embed.set_footer(
                                text=f"You were DMed because you have are currently in a HOI4 game on server "
                                     f"{interaction.guild.name}.")
                            channel = await member.create_dm()
                            await channel.send(embed=embed)

                        except Exception as e:
                            interaction.channel.send(f"❌ Unable to send DM to user {member.mention}")
                            continue
                else:
                    await interaction.channel.send(
                        "❌ The event with this ID does not have any players or the event has already ended."
                        "\nAssign them using the /add_player_list command.")
                    return
            else:
                embed = discord.Embed(title=f"📢 {interaction.guild.name} Announcement!",
                                      description=f"By: {interaction.user}", color=0xff0000)
                embed.add_field(name="Message:", value=message_content, inline=False)
                embed.set_footer(text=f"You were DMed because you have are currently in a HOI4 game on server "
                                      f"{interaction.guild.name}.")
                try:
                    channel = await recipient.create_dm()
                    await channel.send(embed=embed)
                except Exception as e:
                    interaction.channel.send("❌ Unable to send DM to this user.")
                    return
            await interaction.channel.send("✔️ Message sent successfully!")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(announce(client))
