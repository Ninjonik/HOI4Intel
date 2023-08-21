import datetime
import json
import time

import config
import server
from aiohttp import web
from discord.ext import commands
import discord

from presets import _add_player_name, prefix


class ServerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server = server.HTTPServer(
            bot=self.bot,
            host="0.0.0.0",
            port=8089,
        )
        self.bot.loop.create_task(self._start_server())
        self.cursor, self.connection = config.setup()

    async def _start_server(self):
        await self.bot.wait_until_ready()
        await self.server.start()

    @server.add_route(path="/", method="GET", cog="ServerCog")
    async def home(self, request):
        return web.Response(text="working", status=200)

    @server.add_route(path="/get/lobby", method="GET", cog="ServerCog")
    async def edit_guild(self, request):
        payload = await request.json()
        token = payload["token"] if "token" in payload else ''

        if token == config.comms_token:
            lobby_id = int(payload["lobby_id"])
            channel = self.bot.get_channel(lobby_id)
            playersVc = channel.members
            nonBotPlayersVc = [player for player in playersVc if not player.bot]

            playersObj = []

            for player in nonBotPlayersVc:
                rating = await _add_player_name(player.id, player.name, 0.5)
                player_data = {
                    "user": {
                        "discord_id": str(player.id),
                        "discord_name": player.name,
                        "rating": rating,
                        "country": player.display_name,
                        "joined": time.time()
                    },
                    "action": {
                        "none": "none"
                    },
                    "lobby_id": str(lobby_id),
                    "token": config.comms_token
                }
                playersObj.append(player_data)

            response_data = json.dumps(playersObj)
            return web.Response(text=response_data, content_type='application/json')
        else:
            return web.json_response(data={"error": "not authorized"}, status=403)

    @server.add_route(path="/edit/guild", method="PATCH", cog="ServerCog")
    async def edit_guild(self, request):
        payload = await request.json()
        token = payload["token"] if "token" in payload else ''
        if token == config.comms_token:
            guild_id = int(payload["guild_id"])
            guild_name = payload["guild_name"]
            guild_desc = payload["guild_desc"]
            guild = self.bot.get_guild(guild_id)
            try:
                await guild.edit(name=guild_name, description=guild_desc)
                return web.json_response(data={"success": "success"}, status=200)
            except Exception as e:
                return web.json_response(data={"error": e})
        else:
            return web.json_response(data={"error": "not authorized"}, status=403)

    @server.add_route(path="/edit/user", method="PATCH", cog="ServerCog")
    async def edit_guild(self, request):
        payload = await request.json()
        token = payload["token"] if "token" in payload else ''
        if token == config.comms_token:
            guild_id = int(payload["guild_id"])
            player_id = int(payload["player_id"])
            player_new_name = payload["player_new_name"]
            guild = self.bot.get_guild(guild_id)
            player = guild.get_member(player_id)
            try:
                await player.edit(nick=player_new_name)
                return web.json_response(data={"success": "success"}, status=200)
            except Exception as e:
                return web.json_response(data={"error": e})
        else:
            return web.json_response(data={"error": "not authorized"}, status=403)

    @server.add_route(path="/user/ban", method="POST", cog="ServerCog")
    async def ban_user(self, request):
        payload = await request.json()
        token = payload["token"] if "token" in payload else ''
        if token == config.comms_token:
            player_id = int(payload["player_id"])
            host_id = int(payload["host_id"])
            player_name = payload["player_name"]
            reason = payload["reason"]

            await _add_player_name(player_id, player_name, 0.5)
            self.cursor.execute(
                "INSERT INTO bans (player_id, guild_id, host_id, reason, created_at, updated_at) "
                "VALUES(%s, %s, %s, %s, NOW(), NOW())",
                (player_id, 1035627488828735518, host_id, reason)
            )
            for guild in self.bot.guilds:
                try:
                    await guild.ban(discord.Object(id=player_id), reason=reason)
                except Exception as e:
                    print(
                        f"{prefix()} Not enough permissions for banning / User banned | {player_name} on {guild.name}, "
                        f"Host: {host_id}"
                    )
            self.connection.commit()
            return web.json_response(data={"success": "User banned"}, status=200)
        else:
            return web.json_response(data={"error": "not authorized"}, status=403)

    @server.add_route(path="/user/unban", method="PATCH", cog="ServerCog")
    async def unban_user(self, request):
        payload = await request.json()
        token = payload["token"] if "token" in payload else ''
        if token == config.comms_token:
            player_id = int(payload["player_id"])
            reason = payload["reason"]

            self.cursor.execute("DELETE FROM bans WHERE player_id=%s", (player_id,))
            for guild in self.bot.guilds:
                try:
                    await guild.unban(discord.Object(id=player_id), reason=reason)
                except Exception as e:
                    print(
                        f"{prefix()} Not enough permissions for unbanning / User not banned | {player_id} on "
                        f"{guild.name}, Host: -"
                    )
            self.connection.commit()
            return web.json_response(data={"success": "User unbanned"}, status=200)
        else:
            return web.json_response(data={"error": "not authorized"}, status=403)

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

    @server.add_route(path="/get/guild/channels", method="GET", cog="ServerCog")
    async def get_guild_channels(self, request):
        payload = await request.json()
        token = payload.get("token", "")
        if token == config.comms_token:
            guild_id = int(payload["guild_id"])
            guild = self.bot.get_guild(guild_id)
            if payload["voice"]:
                channels = sorted(guild.voice_channels, key=lambda c: c.position)
            else:
                channels = sorted(guild.text_channels, key=lambda c: c.position)
            channel_data = [
                {"channel_name": channel.name, "channel_id": channel.id}
                for channel in channels
            ]

            return web.json_response(data=channel_data, status=200)
        else:
            return web.json_response(data={"error": "not authorized"}, status=403)

    @server.add_route(path="/get/guild/roles", method="GET", cog="ServerCog")
    async def get_guild_channels(self, request):
        payload = await request.json()
        token = payload.get("token", "")
        if token == config.comms_token:
            guild_id = int(payload["guild_id"])
            guild = self.bot.get_guild(guild_id)
            roles = sorted(guild.roles, key=lambda r: r.position)
            role_data = [
                {"role_name": role.name, "role_id": role.id}
                for role in roles
            ]

            return web.json_response(data=role_data, status=200)

        else:
            return web.json_response(data={"error": "not authorized"}, status=403)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ServerCog(client))
