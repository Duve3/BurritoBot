import sys
import discord
from discord import app_commands
from discord.ext import commands, tasks
from log import setupLogging


# all cogs inherit from this base class
class DiscordPresenceCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot  # adding a bot attribute for easier access
        self.statuses = [discord.Game(name="Clash of Clans"), discord.Activity(type=discord.ActivityType.watching, name="you get a 3 star"), discord.Activity(type=discord.ActivityType.watching, name="")]
        self.currentStatus = 0
        self.logger = setupLogging("DiscordPresenceCog")

    @tasks.loop(minutes=1)
    async def ChangeStatus(self):
        await self.bot.change_presence(activity=self.statuses[self.currentStatus])
        self.currentStatus += 1
        if not self.currentStatus <= len(self.statuses) - 1:
            self.currentStatus = 0

    @ChangeStatus.before_loop
    async def wait_login(self):
        await self.bot.wait_until_ready()

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.logger.debug(f"{self.__class__.__name__} loaded!")
        self.ChangeStatus.start()

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you’d use cogs in extensions,
# you would then define a global async function named 'setup' and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(DiscordPresenceCog(bot=bot))
