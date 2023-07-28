import discord
from discord.ext import commands
from discord import app_commands
import config
from presets import _add_player_name
import random

class crash(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.dictionary_setup()

    def getCrashPoint(self) -> float:
        e = 2 ** 32
        h = random.randint(0, e - 1)

        # Set the range for h to be closer to the upper limit e
        # You can adjust the range based on how close you want the output to be to 1
        h = int(0.9 * e + h * 0.1)

        # Introduce a bias to make 1 drop more often
        if h % 20 == 0:
            return 1  # 1 will drop with a probability of 1/20

        # Calculate the crash point
        return (100 * e - h) // (e - h) / 1000

    @app_commands.command(name="crash", description="gamba.")
    async def crash(self, interaction: discord.Interaction, amount: app_commands.Range[float, 1, None], guess: app_commands.Range[float, 1.0, None]):
        self.cursor, self.connection = config.dictionary_setup()

        await _add_player_name(interaction.user.id, interaction.user.name, 0.5)  # If user is not in DB -> add him

        self.cursor.execute("SELECT currency FROM players WHERE discord_id=%s", (interaction.user.id,))

        currency = self.cursor.fetchone()["currency"]

        if (currency < amount): return await interaction.response.send_message("❌ Not enough money!", ephemeral=True)

        oldcurrency = currency
        currency -= amount

        crash_point = self.getCrashPoint()

        if (guess <= crash_point): currency += (amount * guess)

        won = guess <= crash_point

        embed = discord.Embed(title="Crash Result", color=won and 0x00ff40 or 0xff0000)
        embed.add_field(name="Bet/Amount", value=amount, inline=False)
        embed.add_field(name="Guess", value=f"{guess}x", inline=False)
        embed.add_field(name="Crashed At", value=f"{crash_point:.2f}x", inline=False)
        embed.add_field(name="Before", value=oldcurrency, inline=False)
        embed.add_field(name="After", value=currency, inline=False)
        embed.set_image(url=won and "https://compote.slate.com/images/926e5009-c10a-48fe-b90e-fa0760f82fcd.png" or "https://i.imgflip.com/35a1ly.jpg")
        embed.set_footer(text=f"Won: {won}")

        await interaction.response.send_message(embed=embed)

        self.cursor.execute("UPDATE players SET currency=%s WHERE discord_id=%s", (currency, interaction.user.id,))
        self.connection.commit()



async def setup(client: commands.Bot) -> None:
    await client.add_cog(crash(client))
