import logging
from log import setupLogging
import discord
import os
from discord.ext import commands, tasks
import json

# globals
cogPath = "cogs."
debug = False


def getCogs():
    cogList = []
    for file in os.listdir(cogPath.replace(".", "/")):
        if file.endswith(".py") and not file.startswith("DISABLED_") and file != "log.py":
            cogList.append(file.split(".")[0])

    return cogList


class Client(commands.Bot):
    global debug

    def __init__(self):
        global debug
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        with open("./db.json") as db:
            self.db = json.loads(db.read())
        if not debug:
            prefix = "!"
        else:
            prefix = "$$!!"
        super().__init__(
            command_prefix=prefix,
            intents=intents
        )

    # the method to override in order to run whatever you need before your bot starts
    async def setup_hook(self):
        # to avoid cog getting in this list, end it with something other than .py or make it start with "DISABLED_"
        for cog in getCogs():
            await self.load_extension(f"{cogPath}{cog}")

    @tasks.loop(seconds=60)
    async def saveDB(self):
        with open("./db.json", "w+") as db:
            db.write(json.dumps(self.db))
            db.truncate()

    @tasks.loop(seconds=30)
    async def sendQuickConfirmMsg(self):
        logger.debug("bot is online (sent every 30)")

    @sendQuickConfirmMsg.before_loop
    @saveDB.before_loop
    async def waitReadyBeforeLoop(self):
        await self.wait_until_ready()


client = Client()


# makes life easier when changing cogs
@client.command(name="reloadCogs")
async def reloadCogs(ctx):
    if ctx.author.id == 680116696819957810:
        logger.debug("Reloading all cogs!")
        for cog in getCogs():
            await client.unload_extension(f"{cogPath}{cog}")
            await client.load_extension(f"{cogPath}{cog}")
        await ctx.reply("Reloaded all Cogs!")
    else:
        await ctx.reply(f"{ctx.author.mention} :gun:")


@client.event
async def on_ready():
    logger.info(
        f"I have successfully logged in as:\n\t{client.user.name}#{client.user.discriminator}\n\tID: {client.user.id}")


@client.event
async def on_guild_join(guild: discord.Guild):
    """
    On guild added, add to db
    """
    client.db["guilds"][str(guild.id)] = {
        "setup": False,
        "clan": {
            "tag": None,
        },
        "verified": {},
    }


@client.event
async def on_guild_remove(guild: discord.Guild):
    """
    On guild remove, delete from db
    """
    client.db["guilds"][str(guild.id)] = {
        "setup": False,
        "clan": {
            "tag": None,
        },
        "verified": {},
    }


def main():
    global debug
    try:
        with open("token.secret") as tf:
            r = tf.read()
            if len(r.split("\n")) == 2:
                TOKEN = r.split("\n")[1]
                debug = True
            else:
                TOKEN = r.split("\n")[0]
    except FileNotFoundError:
        logger.error("Failed to find token inside of token.secret! Exiting...")
        return
    client.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    # setup
    logger = setupLogging("main", level=logging.DEBUG)
    setupLogging("discord", level=logging.INFO)
    setupLogging("discord.http", level=logging.INFO)
    try:
        # startup
        main()
    finally:
        # cleanup
        with open("./db.json", "w") as db:
            db.write(json.dumps(client.db))
