import discord
from discord.ext import commands
from discord import app_commands
import datetime

import config
from config import redis_connect
from presets import _add_player_name


class Advent(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.guild = None
        self.client = client
        self.gifts = {
            1: {"action": self.gift_action_1, "description": "🎁 A festive role"},
            2: {"action": self.gift_action_2, "description": "🎄 Festive cookies"},
            3: {"action": self.gift_action_3, "description": "🎅 Santa Coins"},
            4: {"action": self.gift_action_3, "description": "🐉 Dragon Coins"},
            5: {"action": self.gift_action_1, "description": "📢 Announcement Pass Role"},
            6: {"action": self.gift_action_3, "description": "👑 WWC Gold Reserves"},
            7: {"action": self.gift_action_nothing, "description": "🤣 Nothing: Come back tomorrow!"},
            8: {"action": self.gift_action_1, "description": "🛷 Christmas sleigh"},
            9: {"action": self.gift_action_1, "description": "🛷 Christmas sleigh"},
        }
        self.cursor, self.connection = config.setup()
        self.redis = redis_connect()

    async def gift_action_nothing(self, user):
        pass

    async def gift_action_1(self, user):
        advent_role = self.guild.get_role(1182416946122211338)
        await user.add_roles(advent_role, reason="Advent")

    async def gift_action_2(self, user):
        await user.send("Day 2 Gift: Giving a special role!")

    async def gift_action_3(self, user):
        await _add_player_name(user.id, user.name, 0.5)
        self.cursor.execute("UPDATE players SET currency = currency + 10000 WHERE discord_id=%s", (user.id,))
        self.connection.commit()

    def get_claimed_users(self, day):
        claimed_users = self.redis.smembers(f"advent:day_{day}")
        return claimed_users

    def set_claimed_user(self, day, user_id):
        self.redis.sadd(f"advent:day_{day}", user_id)

    @app_commands.command(name='advent', description="Claim your daily holiday gift! 🎅🎁")
    async def advent(self, interaction: discord.Interaction):
        if interaction.guild_id == 820918304176340992:
            self.cursor, self.connection = config.setup()
            self.guild = interaction.guild
            today = datetime.datetime.now().day
            gift_data = self.gifts.get(today,
                                       {"action": None, "description": "🎉 Sorry, no gift today. Check back tomorrow!"})

            claimed_users = self.get_claimed_users(today)
            user_id = str(interaction.user.id)

            if user_id not in claimed_users:
                await interaction.response.send_message(f"✨ {interaction.user.mention}, you've claimed today's gift: "
                                                        f"{gift_data['description']} !", ephemeral=True)

                if gift_data["action"]:
                    await gift_data["action"](interaction.user)

                self.set_claimed_user(today, user_id)
            else:
                await interaction.response.send_message(f"☃️ {interaction.user.mention}, "
                                                        f"you've already claimed today's gift!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⛄ Not supported on your server :(", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Advent(client))
