import server
from aiohttp import web
from discord.ext import commands


class ServerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server = server.HTTPServer(
            bot=self.bot,
            host="0.0.0.0",
            port=8089,
        )
        self.bot.loop.create_task(self._start_server())

    async def _start_server(self):
        await self.bot.wait_until_ready()
        await self.server.start()

    @server.add_route(path="/", method="GET", cog="ServerCog")
    async def home(self, request):
        return web.Response(text="working", status=200)

    @server.add_route(path="/get/user/{id}", method="GET", cog="ServerCog")
    async def get_user(self, request):
        user_id = int(request.match_info["id"])
        user = self.bot.get_user(user_id)
        if user is not None:
            user_data = {
                "id": user.id,
                "username": user.name,
                "avatar": str(user.avatar.url),
            }
            return web.json_response(data=user_data, status=200)
        else:
            return web.json_response(data={"error": "User not found"}, status=404)
"""
    @server.add_route(path="/edit/guild", method="PATCH", cog="ServerCog")
    async def edit_guild(self, request):
        payload = await request.json()
        guild_id = int(payload["id"])
        guild_name = payload["name"]
        guild = self.bot.get_guild(guild_id)
        await guild.edit(name=guild_name)

        return web.json_response(data={"success": "success"}, status=200)
"""

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ServerCog(client))