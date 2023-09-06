import sys
import discord
from discord import app_commands
from discord.ext import commands, tasks
from log import setupLogging


# all cogs inherit from this base class
class TemplateCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot  # adding a bot attribute for easier access
        self.logger = setupLogging("TemplateCog")

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.logger.debug(f"{self.__class__.__name__} loaded!")

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you’d use cogs in extensions,
# you would then define a global async function named 'setup' and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(TemplateCog(bot=bot))
