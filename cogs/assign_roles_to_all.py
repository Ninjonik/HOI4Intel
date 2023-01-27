import random

import discord
from discord.ext import commands
from discord import app_commands

import presets


class assign_roles_to_all(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="roles-all", description="Adds selected role to everybody.")
    async def assign_roles_to_all(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.guild_permissions.administrator:
            for member in interaction.guild.members:
                print(role)
                hasRole = False
                print("giving roles")
                for r in member.roles:
                    if r.id == role.id:
                        print("Has role = true")
                        hasRole = True
                if not hasRole:
                    print(f"Giving role to {member}")
                    try:
                        await member.add_roles(role)
                    except Exception as e:
                        print(e)
            await interaction.response.send_message(content="Command successfully executed!", ephemeral=True)
        else:
            await interaction.response.send_message(content="Not enough permissions for this command!", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(assign_roles_to_all(client))
