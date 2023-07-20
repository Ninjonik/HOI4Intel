import time

from discord.ext import commands
import discord
import datetime
import config
import openai

openai.api_key = config.openai_api_key
openai.api_base = config.openai_api_base

# Define the cooldown
image_cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user)

class Image(commands.Cog):
    def __init__(self, client):
        self.client = client

    def get_ratelimit_key(self, ctx):
        return ctx.author.id  # Use the user ID as the key for the cooldown bucket

    @commands.command(name='image', description="Generates an image based on the prompt.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image(self, ctx: commands.Context, *, prompt: str):
        channel = ctx.channel
        await ctx.send("⏳ Generating...")
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        # Create a Discord embed
        embed = discord.Embed(title="AI Generated Image")
        embed.add_field(name="Prompt: ", value=prompt)

        # Add the images to the embed
        for image in response.data:
            embed.set_image(url=image['url'])

        # Send the embed message with the images
        await channel.send(embed=embed)

    # Define the error handling for the cooldown
    @image.error
    async def image_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = round(error.retry_after)
            await ctx.send(f"❌ Command on cooldown. Please try again in {retry_after} second(s).")

    # Override the get_cooldown_retry_after method to use a custom cooldown for the slash command
    async def get_cooldown_retry_after(self, ctx):
        bucket = image_cooldown.get_bucket(ctx.message)
        current = time.time()
        cooldown = bucket._cooldown.per
        retry_after = cooldown - (current - bucket.update_rate_limit())
        return retry_after

def setup(client: commands.Bot) -> None:
    client.add_cog(Image(client))
