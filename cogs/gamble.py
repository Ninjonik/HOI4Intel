import discord
from discord.ext import commands
from discord import app_commands
import config
from presets import _add_player_name
import random

class gamble(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.dictionary_setup()
        self._slots = [
            {
                "multiplier": 0,
                "weight": 600
            },
            {
                "multiplier": 2,
                "weight": 250
            },
            {
                "multiplier": 3,
                "weight": 100
            },
            {
                "multiplier": 5,
                "weight": 50
            },
            {
                "multiplier": 10,
                "weight": 1
            },
            {
                "multiplier": 100,
                "weight": 0.1
            }
        ]

    def getTotalWeight(self) -> float:
        return sum(slot["weight"] for slot in self._slots)

    def getRandomSlot(self) -> int:
        total_weight = self.getTotalWeight()
        random_number = random.random() * total_weight

        for slot in self._slots:
            if random_number <= slot["weight"]:
                return slot["multiplier"]
            else:
                random_number -= slot["weight"]

        # If the loop completes without returning a slot, return the last one as a fallback
        return self._slots[-1]["multiplier"]

    @app_commands.command(name="gamble", description="gamba.")
    async def gamble(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, None]):
        self.cursor, self.connection = config.dictionary_setup()
        player = interaction.user
        await _add_player_name(interaction.user.id, interaction.user.name, 0.5)  # If user is not in DB -> add him

        self.cursor.execute("SELECT currency FROM players WHERE discord_id=%s", (player.id,))
        currency = self.cursor.fetchone()["currency"]
        if currency < amount:
            await interaction.response.send_message("❌ Not enough money!", ephemeral=True)
            return

        oldcurrency = currency

        currency -= amount

        multiplier = self.getRandomSlot()

        currency += (amount * multiplier) or 0

        await interaction.response.send_message(f"Start {oldcurrency} \nNew {currency} \nMultiplier {multiplier}x")

        self.cursor.execute("UPDATE players SET currency=%s WHERE discord_id=%s", (currency, player.id,))
        self.connection.commit()

async def setup(client: commands.Bot) -> None:
    await client.add_cog(gamble(client))
