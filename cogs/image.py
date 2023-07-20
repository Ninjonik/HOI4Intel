import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config
import openai

openai.api_key = config.openai_api_key
openai.api_base = config.openai_api_base


class image(commands.Cog):
    @app_commands.command(name='image', description="Generates image based on the prompt.")
    async def image(self, interaction: discord.Interaction, prompt: str):
        channel = interaction.channel
        await interaction.response.send_message("⏳ Generating...", ephemeral=True)
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        # Create a Discord embed
        embed = discord.Embed(title="AI Generated Image")

        # Add the images to the embed
        for image in response.data:
            embed.set_image(url=image['url'])

        # Send the embed message with the images
        await channel.send(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(image(client))
