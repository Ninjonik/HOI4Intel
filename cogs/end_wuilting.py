import datetime

import discord
from discord.ext import commands
from discord import app_commands

import config


class EndWuilting(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="end_wuilting")
    async def end_wuilting(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            guild = interaction.guild
            r = config.redis_connect()
            wuilting_channel_id = r.hget(f'guild:{str(interaction.guild.id)}', 'wuilting_channel_id')

            if wuilting_channel_id:

                await interaction.response.send_message("👷 Working on it...", ephemeral=True)

                wuilting_channel = interaction.guild.get_channel(int(wuilting_channel_id))

                final_text = ""
                for i in range(r.llen(f'guild:{str(interaction.guild.id)}:wuilting')):
                    final_text += str(r.lpop(f'guild:{str(interaction.guild.id)}:wuilting')) + " "

                r.rpush(f"guild:{str(guild.id)}:wuilting", final_text)

                if len(final_text) > 950:
                    fields = (len(final_text) // 950) + 1
                else:
                    fields = 1

                await wuilting_channel.purge(limit=100)
                embed = discord.Embed(
                    title="🌟 Welcome to the Wuilting! 🚀",
                    description="Embark on a linguistic journey with a twist! 📜✨",
                    color=0x3498db
                )

                i = 0
                for field in range(fields):
                    if i == 0:
                        embed.add_field(
                            name="**Last Wuilting:**",
                            value=f"{final_text[:950]}",
                            inline=False
                        )
                        final_text = final_text[950:]
                    else:
                        embed.add_field(
                            name="​",
                            value=f"{final_text}",
                            inline=False
                        )
                        final_text = final_text[950:]
                    i += 1

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

                embed.set_footer(text=f"⏰ Last wuilting cycle end-time: "
                                      f"{datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')} ")

                embed.set_thumbnail(url=guild.icon)
                await wuilting_channel.send(embed=embed)

                await interaction.channel.send("✔️ Wuilting cycle ended successfuly!")

            else:
                await interaction.response.send_message(f"❌ Wuilting channel not set up in the settings!")




        else:
            await interaction.response.send_message(
                "❌ Not enough permissions!",
                ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(EndWuilting(client))
