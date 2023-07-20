import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config
import openai

openai.api_key = config.openai_api_key
openai.api_base = config.openai_api_base

cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user)


class image(commands.Cog):
    @app_commands.command(name='image', description="Generates image based on the prompt.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image(self, interaction: discord.Interaction, prompt: str):
        if len(prompt) > 30:
            await interaction.response.send_message("❌ Too long prompt!")
            return
        channel = interaction.channel
        await interaction.response.send_message("⏳ Generating...", ephemeral=True)
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        # Create a Discord embed
        embed = discord.Embed(title="AI Generated Image")
        embed.add_field(name="Prompt: ", value=prompt)
        embed.add_field(name="Prompted by:", value=interaction.user.mention)

        # Add the images to the embed
        for image in response.data:
            embed.set_image(url=image['url'])

        # Send the embed message with the images
        await channel.send(embed=embed)

    @image.error
    async def image_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = round(error.retry_after)
            await ctx.send(f"❌ Command on cooldown. Please try again in {retry_after} second(s).")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(image(client))
