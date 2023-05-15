import discord
from discord.ext import commands
from discord import app_commands
import config


class RequestSteam(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="request_steam")
    async def request_steam(self, interaction: discord.Interaction, player: discord.User):
        self.cursor, self.connection = config.setup()
        if interaction.user.guild_permissions.administrator:
            self.cursor.execute("SELECT profile_link FROM players WHERE discord_id=%s", (player.id,))
            profile_link = self.cursor.fetchone()
            if profile_link[0] is not None:
                await interaction.response.send_message(
                    f"ℹ️ This user is already verified."
                    f"\nHis profile link: {profile_link[0]}")
                return
            try:
                channel = await player.create_dm()
                await channel.send(name="Steam Verification",
                             value=f"You were DMed because {interaction.guild.name}'s Host"
                             f" {interaction.user.mention} is requesting you to verify your steam account."
                             f"\nYou can do so by going on HOI4Intel's secure website: "
                             f"https://hoi.theorganization.eu/steam/{player.id}")
                await interaction.response.send_message("✔️ Message sent successfully!")
            except Exception as e:
                await interaction.response.send_message("❌ Unable to send DM to this user.")
                print(e)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(RequestSteam(client))
