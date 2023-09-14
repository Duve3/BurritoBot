import sys

import discord
from discord.ext import commands

from log import setupLogging


def isATypeOfYes(msg: str):
    typeOfYeses = [
        "yes",
        "y",
        "ye",
        "ya",
        "yah",
        "yea",
        "yeh",
        "yeah",
        "yessir"
    ]
    if msg.lower() in typeOfYeses:
        return True
    return False


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = setupLogging("OwnerCog")

    @commands.command(name="sync")
    async def sync(self, ctx):
        messageStuff = ctx.message.content.split(" ")
        messageStuff.pop(0)
        if ctx.author.id == 680116696819957810:
            if len(messageStuff) != 0:
                self.logger.info(f"Syncing app commands to {ctx.message.guild.id}")
                await ctx.reply("Syncing app commands to this guild!")
                await self.bot.tree.sync(guild=discord.Object(ctx.message.guild.id))
                await ctx.reply("Successfully synced app commands to this guild!")
            else:
                def check(message):
                    return message.author == message.author
                self.logger.info("Owner has asked to sync, awaiting confirmation.")
                await ctx.reply("Are you sure you want to sync app commands GLOBALLY? This process can take up to an hour!")
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                if isATypeOfYes(msg.content):
                    self.logger.info(f"Syncing app commands globally")
                    await ctx.reply("Syncing app commands globally, can take up to an hour.")
                    await self.bot.tree.sync()
                else:
                    self.logger.info(f"Owner denied sync.")
                    await ctx.reply("No longer syncing app commands globally. \nIf your trying to sync at a guild level check your goofy code.")
        else:
            await ctx.reply('You must be the owner to use this command!')

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.logger.debug(f"{self.__class__.__name__} loaded!")

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you’d use cogs in extensions
# you would then define a global async function named 'setup', and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(OwnerCog(bot=bot))
