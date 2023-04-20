import discord
from discord.ext import commands
from discord import app_commands
import config

class add_blog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.cursor, self.connection = config.setup()

    @app_commands.command(name="add_blog", description="Create a new blog-post for the website. It has to be approved "
                                                       "by HOI4 Moderators first.")
    @app_commands.describe(title='Example: "New Feature! Event System"',
                           description='Content of the blog post.')
    async def add_blog(self, interaction: discord.Interaction, title: str, description: str):
        if interaction.user.guild_permissions.administrator and title and description:
            self.cursor, self.connection = config.setup()
            await interaction.response.send_message("Blog added successfully!", ephemeral=True)
            # Store datetime and timezone in MySQL database
            sql = "INSERT INTO events (author_id, title, description, approved, created_at, updated_at) " \
                  "VALUES (%s, %s, %s, 0, NOW(), NOW())"
            values = (interaction.user.id, title, description)
            self.cursor.execute(sql, values)
            self.connection.commit()
        else:
            await interaction.response.send_message("There has been an error while handling your request.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(add_blog(client))
