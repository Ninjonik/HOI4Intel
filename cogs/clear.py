import discord
from discord.ext import commands
from discord import app_commands


class clear(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="clear", description="Clears last x messages in a channel")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(content=f"{amount} messages have been removed.")
            await interaction.channel.purge(limit=amount+1)
        else:
            await interaction.response.send_message(content=f"Not enough permissions for this command!", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(clear(client))
