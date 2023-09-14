import asyncio
import sys
import discord
from discord import app_commands
from discord.ext import commands, tasks
from log import setupLogging
import requests
import urllib.parse
import datetime


def check(message):
    def inner_check(author):
        return message.author == author

    return inner_check


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


# all cogs inherit from this base class
class ClashOfClansCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot  # adding a bot attribute for easier access
        self.logger = setupLogging("ConnectPlayerCog")
        self.clanEndpoint = "https://api.clashofclans.com/v1/clans/"
        self.playerEndpoint = "https://api.clashofclans.com/v1/players/"
        self.coLeaderID = 1147269041912807456
        self.elderID = 1147269095469879316
        self.memberID = 1147269120480526386
        self.townhallRoleIDS = [1148397352055472178, 1148397270757298256, 1148397177660510218, 1148397103429734410,
                                1148397061620891718, 1148397016674750574, 1148396963490971749, 1148396901096493096,
                                1148396853134630919, 1148396804979838997, 1148396705071497226, 1148702683327377591,
                                1148702765825130597, 1148702832967548959, 1148702974542094488, 1148703008910221413]
        self.in_warVCID = 1148727256726917201
        self.current_starsVCID = 1148727406434189362
        with open("./api.secret") as apif:
            self.key = apif.read()
        self.db = self.bot.db  # noqa:missing ; it should exist, if not then error is good

    # @commands.command(name="test")
    # async def test(self, a: int):
    #     await self.bot.wait_until_ready()
    #     for i, role in enumerate(self.townhallRoleIDS):
    #         guild = self.bot.get_guild(1147266129807544431)
    #         r = guild.get_role(role)
    #         self.logger.debug(f"number: {i} name: {r.name}")

    def getClanData(self, tag):
        res = requests.get(f"{self.clanEndpoint}{urllib.parse.quote(tag)}",
                           headers={'Authorization': f'Bearer {self.key}'})
        if res.status_code == 200:
            res = res.json()

            return res
        else:
            self.logger.error("Something went wrong when getting coc data")
            self.logger.debug(res.json())
            return res.json()

    def refreshClanData(self, gid):
        guild = self.db["guilds"][str(gid)]
        tag = guild["clan"]["tag"]
        res = self.getClanData(tag)

        self.db["guilds"][str(gid)]["clan"] = res

    def getPlayerData(self, tag):
        res = requests.get(f"{self.playerEndpoint}{urllib.parse.quote(tag)}",
                           headers={'Authorization': f'Bearer {self.key}'})

        if res.status_code == 200:
            res = res.json()

            self.logger.debug(res)
            return res
        else:
            self.logger.error("Something went wrong when getting coc data")
            self.logger.debug(res.json())
            return res.json()

    async def updateWarStats(self, gid):
        war_stats = self.bot.get_channel(self.in_warVCID)
        star_count = self.bot.get_channel(self.current_starsVCID)
        res = requests.get(
            f"{self.clanEndpoint}{urllib.parse.quote(self.db['guilds'][str(gid)]['clan']['tag'])}/currentwar",
            headers={'Authorization': f'Bearer {self.key}'})

        if res.status_code == 200:
            res = res.json()
        else:
            self.logger.error("Updating war stats went wrong, here's debug info (turn on debug btw):")
            self.logger.debug(res.json())
            self.logger.debug(res)
            return

        if res["state"].upper() == "NOT_IN_WAR":
            await war_stats.edit(name="War Status: Not in war")
            await star_count.edit(name="Star Count: Not in war")

        elif res["state"].upper() == "IN_MATCHMAKING":
            await war_stats.edit(name="War Status: Matchmaking")
            await star_count.edit(name="Star Count: Matchmaking")

        elif res["state"].upper() == "PREPARATION":
            await war_stats.edit(name="War Status: Preparation")
            await star_count.edit(name="Star Count: Preparation")

        elif res["state"].upper() == "IN_WAR":
            await war_stats.edit(name="War Status: In War")
            sc = res["stars"]
            await star_count.edit(name=f"Star Count: {sc}")

    @tasks.loop(minutes=5)
    async def updateStatsPerGuild(self):
        for g in self.db["guilds"].keys():
            if not self.db["guilds"][str(g)]["setup"]:
                continue

            await self.updateWarStats(g)
            await asyncio.sleep(
                15)  # waits 15 seconds after each update, so make sure we don't hit an API limit, this is on top of the 5 minutes per guild

    @updateStatsPerGuild.before_loop
    async def waitForLoad(self):
        await self.bot.wait_until_ready()

    async def verifyPlayer(self, username, gid, uid):
        guild = self.db["guilds"][str(gid)]
        clan = guild["clan"]

        for member in clan["memberList"]:
            if member["name"].lower() == username.lower():  # .lower() to avoid people typoing
                if member["name"].lower() in guild["verified"].values():
                    return "ERROR: this username has already been verified!"
                else:
                    guild["verified"][str(uid)] = username
                    member = self.getPlayerData(member["tag"])
                    server = self.bot.get_guild(gid)
                    gMember = server.get_member(uid)
                    reason = "CoC automatic role add from verification"
                    # leader/coleader/elder/member automatic role addition
                    if member["role"].lower() == "coleader":
                        role = server.get_role(self.coLeaderID)  # gets the "CoLeader" Role
                        await gMember.add_roles(role, reason=reason)

                    elif member["role"].lower() == "admin":
                        role = server.get_role(self.elderID)
                        await gMember.add_roles(role, reason=reason)

                    elif member["role"].lower() == "member":
                        role = server.get_role(self.memberID)
                        await gMember.add_roles(role, reason=reason)

                    elif member["role"].lower() == "leader":
                        return "ERROR: in order to verify as clan leader, you will have to directly DM a server admin. This is for security reasons."

                    # automatic townhall roles
                    role = server.get_role(self.townhallRoleIDS[member["townHallLevel"] - 1])
                    await gMember.add_roles(role, reason=reason)

                    return True

        return "ERROR: this user does not exist in the clan!"

    @commands.hybrid_command(name="connect_player", description="A command to connect your discord to CoC user.")
    async def connectPlayer(self, ctx: commands.Context, username: str):
        if not self.db["guilds"][str(ctx.guild.id)]["setup"]:
            await ctx.reply("ERROR: The clan for this guild has not been set!")
            return

        if str(ctx.author.id) in self.db["guilds"][str(ctx.guild.id)]["verified"].keys():
            await ctx.reply("ERROR: you have already verified your account!")
            return
        # refresh clan data
        self.refreshClanData(ctx.guild.id)
        res = await self.verifyPlayer(username, ctx.guild.id, ctx.author.id)
        if res is not True:
            await ctx.reply(res)
            return
        await ctx.reply("Alright you have been verified!")

    @commands.command(name="owner_connect_player")
    async def ownerConnectPlayer(self, ctx: commands.Context, uid: int, username: str):
        if ctx.author.id == 680116696819957810:
            if not self.db["guilds"][str(ctx.guild.id)]["setup"]:
                await ctx.reply("ERROR: The clan for this guild has not been set!")
                return

            if str(uid) in self.db["guilds"][str(ctx.guild.id)]["verified"].keys():
                await ctx.reply("ERROR: you have already verified your account!")
                return
            # refresh clan data
            self.refreshClanData(ctx.guild.id)
            res = await self.verifyPlayer(username, ctx.guild.id, uid)
            if res is not True:
                await ctx.reply(res)
                return
            await ctx.reply(f"Alright I have verified {uid} with {username}")
        else:
            await ctx.reply(":gun:")

    @commands.hybrid_command(name="setup_guild", description="A command to setup your guild to work with this bot.")
    @commands.has_permissions(manage_roles=True, kick_members=True)
    async def setupGuild(self, ctx: commands.Context, tag: str):
        if self.db["guilds"][str(ctx.guild.id)]["setup"]:
            await ctx.reply("ERROR: This guild has already been setup, to setup again remove then add back bot")
            return

        await ctx.reply("Please wait (you will be asked for confirmation)")
        res = self.getClanData(tag)

        await ctx.reply(f"Please confirm if your clan name is: '{res['name']}'")

        msg = await self.bot.wait_for('message', check=check, timeout=30)  # noqa ; (idk why it shows up)

        if msg.content.lower() in typeOfYeses:
            self.db["guilds"][str(ctx.guild.id)]["setup"] = True
            self.db["guilds"][str(ctx.guild.id)]["clan"] = res

            await ctx.reply("Your server is now setup!")
            return
        else:
            await ctx.reply("Ok, your server isn't setup, run the command again to retry the setup.")
            return

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.updateStatsPerGuild.start()
        self.logger.debug(f"{self.__class__.__name__} loaded!")

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you’d use cogs in extensions,
# you would then define a global async function named 'setup' and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(ClashOfClansCog(bot=bot))
