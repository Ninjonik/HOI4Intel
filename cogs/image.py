import discord
from discord.ext import commands
from discord import app_commands
import config
import openai

openai.api_key = config.openai_api_key
openai.api_base = config.openai_api_base

cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user)


class image(commands.Cog):
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.command(name='image', description="Generates image based on the prompt.")
    async def image(self, interaction: discord.Interaction, prompt: str, count: app_commands.Range[int, 1, 5]):
        if len(prompt) > 100:
            await interaction.response.send_message("❌ Too long prompt!")
            return
        channel = interaction.channel
        await interaction.response.send_message("⏳ Generating...", ephemeral=True)
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=count,
                size="1024x1024"
            )
        except Exception as e:
            await interaction.channel.send('❌')
            return

        for image in response.data:
            embed = discord.Embed(title="AI Generated Image")
            embed.add_field(name="Prompt: ", value=prompt)
            embed.add_field(name="Prompted by:", value=interaction.user.name)
            embed.set_image(url=image['url'])
            await channel.send(embed=embed)



    @image.error
    async def image_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = round(error.retry_after)
            await ctx.send(f"❌ Command on cooldown. Please try again in {retry_after} second(s).")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(image(client))
