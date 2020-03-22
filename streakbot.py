import discord
import json
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime
from database import DataBase
import dbl

from discord.ext.commands import CommandError

bot = commands.Bot(command_prefix='!')


#streakData = json.load(open("streak.json", "r+"))


class StreakBot(commands.Cog):
    today = datetime.today().date().strftime("%d-%m-%Y")
    yesterday = None

    def __init__(self, bot):
        self.bot = bot
        self.embed = None
        self.token = ""
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

        self.dataBase = DataBase('discordStreakBot.db')
        self.dataBase.createTable()
        self.dataBase.createGlobalTable()
       # self.migrationToSQL()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}\n')
        self.dateCheck.start()


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Stop raising error for commands bugs to much
        """
        if isinstance(error, CommandError):
            return
        raise error
    async def on_guild_post(self):
        print("Server count posted successfully")

    # def migrationToSQL(self):
    #     for guildID in streakData:
    #         serverThreshold = streakData[guildID]['serverInfo']["wordcount"]
    #         guildID = guildID
    #
    #         for userID in streakData[guildID]:
    #             try:
    #                 if userID != 'serverInfo':
    #                     msgCount = streakData[guildID][userID][0]
    #                     streakCounter = streakData[guildID][userID][1]
    #                     streaked = 1 if streakData[guildID][userID][2] else 0
    #                     highestStreak = streakData[guildID][userID][3]['highestStreak']
    #                     lastStreakDay = streakData[guildID][userID][3]['lastStreakDay']
    #                     highestMessageCount = streakData[guildID][userID][3]['highestMessageCount']
    #                     self.dataBase.addJsonGuildToSQL(guildID, serverThreshold, userID, msgCount, streakCounter,
    #                                                     streaked,
    #                                                     highestStreak, lastStreakDay, highestMessageCount)
    #
    #             except IndexError:
    #                 pass
    #
    #     self.dataBase.commit()

    @commands.Cog.listener()
    async def on_message(self, message):

        user = message.author
        userID = user.id
        guildID = message.guild.id
        guild = message.guild

        # ignore bots
        if not user.bot:

            messageLength = len(message.content.split())
            # add the length of the message to the database to track
            self.dataBase.addMessageCount(guildID, userID, messageLength)
            # retrieve user message count
            # try and retrieve message count
            try:
                msgCount = self.dataBase.getMessageCount(guildID, user.id)
            except TypeError:
                # if it doesnt exist means user doesn't exist
                self.dataBase.addUser(guild, user)
                # now retrieve the user's message count
                msgCount = self.dataBase.getMessageCount(guildID, user.id)

            # retrieve server message threshold
            guildThreshold = self.dataBase.getServerThreshold(guildID)
            # check if they had streaked
            streaked = self.dataBase.checkUserStreaked(guildID, userID)

            # get stats for the global version
            streakedGlobal = self.dataBase.checkUserGlobalStreaked(userID)
            globalThreshold = self.dataBase.getGlobalThreshold()
            msgCountGlobal = self.dataBase.getMessageCountGlobal(userID)


            self.fillNoneData(message.guild, user)

            # give streak if they had streaked.
            if msgCount >= guildThreshold and not streaked:
                self.dataBase.addStreakToUser(guildID, userID, self.today)

            if msgCountGlobal >= globalThreshold and not streakedGlobal:
                self.dataBase.addGlobalStreakUser(userID, self.today)

    # this is temporary till all none data is filled
    def fillNoneData(self, guild, user):
        # updating ServerName, will be used to update Database for old info  (temporary will be removed once it has been
        # updated
        guildName = self.dataBase.updateServerName(guild) if self.dataBase.getServerName(guild) is None \
            else self.dataBase.getServerName(guild)

        userName = self.dataBase.updateUserName(user) if self.dataBase.getUserName(user) is None \
            else self.dataBase.getUserName(user)

    @commands.command()
    async def streak(self, ctx, *args):

        # getting the guild the message was sent from

        guildID = ctx.guild.id

        # check if user has mentioned someone
        mention = ctx.message.mentions

        # get the first word this will be used for $streak me to retrieve current user's streak
        otherMessage = args

        # if user has mentioned someone return the first mention in case they mentioned more than once
        if mention:
            # get the user that was mention
            userMentioned = mention[0]
            # check if the user mentioned is a bot other wise cancel
            if not mention[0].bot:
                # send the information over to another method to send an embed for that user
                # passing over ctx to send message to the channel

                await self.mentionStreak(ctx, userMentioned, guildID)

        # check if there's any other messages that were sent
        elif otherMessage:

            # get the first word that was mentioned
            otherMessage = args[0]

            if otherMessage == "me":
                await self.mentionStreak(ctx, ctx.author, guildID)

            elif otherMessage == "global":
                await self.globalLeaderBoard(ctx)
        else:

            # return first 25
            leaderBoard = self.dataBase.viewServerLeaderBoard(guildID)

            # get the username of a user and remove anything after their deliminator #

            userNames = []
            for data in leaderBoard:
                serverID = data[0]
                serverName = data[1]
                userName = data[2]
                userID = data[3]
                if userName is None:
                    try:
                        self.dataBase.updateUserName(self.bot.get_user(userID))
                        userNames.append(self.bot.get_user(userID).name)
                    except AttributeError:
                        self.dataBase.removeUser(serverID, userID)
                else:
                    # remove the deliminator as we would only need the name
                    userNames.append(userName.split('#')[0])

                if serverName is None:
                    self.dataBase.updateServerName(self.bot.get_guild(serverID))

            userNames = '\n'.join(userNames)

            usersTotalMessages = '\n'.join([str(user[4]) for user in leaderBoard])
            usersStreakDays = '\n'.join([str(user[5]) for user in leaderBoard])

            self.embed = dict(
                title=f"**==STREAK LEADERBOARD==**",
                color=9127187,
                thumbnail={
                    "url": "https://cdn4.iconfinder.com/data/icons/miscellaneous-icons-2-1/200/misc_movie_leaderboards3-512.png"},
                fields=[dict(name="**Users**", value=userNames, inline=True),
                        dict(name="Streak Total", value=usersStreakDays, inline=True),
                        dict(name="Total Words Sent", value=usersTotalMessages, inline=True)],
                footer=dict(text=f"Total Words counted on {self.today} ")
            )
            await ctx.channel.send(embed=discord.Embed.from_dict(self.embed))

    async def globalLeaderBoard(self, ctx):
        # return first 25
        leaderBoard = self.dataBase.viewGlobalLeaderBoard()
        # get the username of a user and remove anything after their deliminator #
        # userNames = '\n'.join([user[1].split('#')[0] for user in leaderBoard])

        userNames = []

        for data in leaderBoard:
            serverID = data[0]
            serverName = data[1]
            userName = data[2]
            userID = data[3]
            if userName is None:
                self.dataBase.updateUserName(self.bot.get_user(userID))
                userNames.append(self.bot.get_user(userID).name)
            else:
                userNames.append(userName)

            if serverName is None:
                self.dataBase.updateServerName(self.bot.get_guild(serverID))

        userNames = '\n'.join(userNames)

        usersTotalMessages = '\n'.join([str(user[4]) for user in leaderBoard])
        usersStreakDays = '\n'.join([str(user[5]) for user in leaderBoard])

        self.embed = dict(
            title=f"**==GLOBAL STREAK LEADERBOARD==**",
            color=9127187,
            thumbnail={
                "url": "https://cdn4.iconfinder.com/data/icons/miscellaneous-icons-2-1/200/misc_movie_leaderboards3-512.png"},
            fields=[dict(name="**Users**", value=userNames, inline=True),
                    dict(name="Streak Total", value=usersStreakDays, inline=True),
                    dict(name="Total Words Sent", value=usersTotalMessages, inline=True)],
            footer=dict(text=f"Total Words counted on {self.today} | Threshold for Global is 500 word Count")
        )
        await ctx.channel.send(embed=discord.Embed.from_dict(self.embed))

    # checking for the dates if its a new day
    @tasks.loop(minutes= 5)
    async def dateCheck(self):

        currentDay = datetime.today().date().strftime("%d-%m-%Y")

        #currentDay = '23/03/2020'
        print(self.today)
        if self.today != currentDay:
            # keeping tracking of the day  before
            yesterday = self.today
            # updating today so it is the correct date
            self.today = currentDay
            self.dataBase.setNewDayStats()

            print("New Day")

    @commands.Cog.listener()
    async def on_member_join(self, user):

        # add the user to the correct server
        if not user.bot:
            print(f"New user has joined {user.guild.name}")
            self.dataBase.addUser(user.guild, user)

    @commands.Cog.listener()
    async def on_member_remove(self, user):

        # remove the user from data as they have left
        if not user.bot:
            print(f"user has left  {user.guild.name}")
            self.dataBase.removeUser(user.guild.id, user.id)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        print(f"New Guild Has Joined {guild.name}")
        # add new guild to the database
        self.dataBase.addNewGuild(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        print(f"A Guild Has left {guild.name}")
        self.dataBase.removeServer(guild.id)

    @commands.command()
    async def info(self, ctx):

        # how many server the bot is in
        totalGuilds = len(self.bot.guilds)
        # how many user the bot can see (including bots)
        totalUsers = len(self.bot.users)

        totalChannels = sum([len(guild.channels) for guild in self.bot.guilds])

        latency = int(self.bot.latency * 100)

        guildID = ctx.guild.id

        # the threshold(total messages to achieve to streak) the guild has been set to
        guildThreshold = self.dataBase.getServerThreshold(guildID)

        self.embed = dict(
            title=f"**==DISCORD STREAK INFO==**",
            color=9127187,
            description=
            f":white_small_square: Minimum word count for streak is {guildThreshold:0,}.\n"
            f":white_small_square: Streaks are added when you reach {guildThreshold:0,} words or more.\n"
            ":white_small_square: Streak will reset at midnight GMT failure to meet word count.\n"
            ,
            thumbnail={
                "url": "https://cdn3.iconfinder.com/data/icons/shopping-e-commerce-33/980/shopping-24-512.png"},
            fields=[dict(name=f"**====================** \n"
                         , value=f":book: Total Servers\n"
                                 f":book: Total Players\n"
                                 f":book: Total Channels\n"
                                 f":book: My Connection\n"
                                 "====================", inline=True),

                    dict(name="**====================**", value=f":white_small_square:    {totalGuilds}\n "
                                                                f":white_small_square:    {totalUsers:02,}\n"
                                                                f":white_small_square:    {totalChannels:02,}\n"
                                                                f":white_small_square:    {latency} ms\n"
                                                                f"====================",
                         inline=True),

                    dict(name="**Useful Links**",
                         value=f":white_small_square: [Vote](https://top.gg/bot/685559923450445887) for the bot \n"
                               f":white_small_square: [support channel](https://discord.gg/F6hvm2) for features request| upcoming updates"
                         ,
                         inline=False),

                    dict(name="**Update**",
                         value=f":white_small_square: **!streak global** NEW COMMAND SEE GLOBAL LEADERBOARD\n"
                            f":white_small_square: **!streak @someone** to view their summary profile\n"
                               f":white_small_square: **!streak me** to view your own profile \n"
                               f":white_small_square: small Achievement has been added summary profile.\n"
                               f":white_small_square: set threshold for amount words for a streak **!threshold amount** \n"
                               f":white_small_square: **only server owner can set threshold**\n",

                         inline=False),

                    ],

            footer=dict(text=f"HAPPY STREAKING!"),
        )
        await ctx.channel.send(embed=discord.Embed.from_dict(self.embed))

    async def mentionStreak(self, ctx, user, guildID):

        userName, MsgCount, streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount \
            = self.dataBase.getUserInfo(guildID, user.id)


        guildThreshold = self.dataBase.getServerThreshold(guildID)

        # adding emotes based on different stages of streak for current streak only
        # if user has reached 3 or more streak day they get fire streak
        if streakCounter >= 3:

            userStreakFormat = f"{streakCounter} :fire:"

            #  if user reached over 100 streaks they get #100 emote
            if streakCounter >= 100:
                userStreakFormat = f"{streakCounter} :fire: :100: "

        else:
            userStreakFormat = streakCounter

        # message to be put in the footer if they had achieved a streak
        streakClaimedMessage = "You have claimed your streak for today"

        # footer message to indicate if the user has received a streak for today
        footerMessage = streakClaimedMessage if MsgCount >= guildThreshold else f"Word count till streak {guildThreshold - MsgCount}" \
 \
            # userTotalMessages = userTotalMessages if userTotalMessages < 100 else f"{userTotalMessages} "

        self.embed = dict(
            color=9127187,
            author={"icon_url": f"{user.avatar_url}", "url": f"{user.avatar_url}",
                    "name": f"{userName}'s Profile Summary"},
            fields=[
                dict(name="**Highest Streak**", value=highestStreak, inline=True),
                dict(name="**Current Streak**", value=userStreakFormat, inline=True),
                dict(name=":book: **Other Stats**",
                     value=f":small_blue_diamond: **Last Streaked:**  \u200b {lastStreakDay}\n"
                           f":small_blue_diamond: **Current Word Count:**  \u200b {MsgCount:0,}\n"
                           f":small_blue_diamond: **Total Word Count:**  \u200b {highMsgCount:0,}",
                     inline=False),

            ],
            # image = {"url": f"{user.avatar_url}"},
            # footer
            footer=dict(text=f"{footerMessage}"),

        )


        # check if the user has achieved any of the milestones
        self.achievementUnlocks(highestStreak, highMsgCount)

        await ctx.channel.send(embed=discord.Embed.from_dict(self.embed))

    def achievementUnlocks(self, userStreak, totalMessage):

        # milestone that will be used for looping
        milestones = {10: "",
                      20: "",
                      40: "",
                      60: "",
                      80: "",
                      100: "",
                      150: ""}

        msgMilestone = {500: "",
                        1000: "",
                        10000: "",
                        50000: "",
                        100000: "",
                        250000: "",
                        500000: ""}

        # loop through the milestone and check if the user has reached the milestone if they have give them diamond
        # else cross


        achievementStreakCheck = '\n'.join([f":gem: {milestone} Streaks" if userStreak >= milestone else f":x: {milestone} Streaks" for milestone in milestones])

        achievementMsgCheck = '\n'.join([
            f":gem: {milestone:02,} words" if totalMessage >= milestone else f":x: {milestone:02,} words"
            for milestone in msgMilestone])

        # add the achievement to the embed to display
        achievements = dict(name="**Streak Milestones**",
                            value=f"{achievementStreakCheck}", inline=True)

        achievement2 = dict(name="**Words Milestones**",
                            value=f"{achievementMsgCheck}", inline=True)

        bottomBar = dict(name="=====**More Achievements To Come**====", value=f"\u200b")

        self.embed['fields'].append(achievements)
        self.embed['fields'].append(achievement2)
        self.embed['fields'].append(bottomBar)

    @commands.command()
    async def threshold(self, ctx, total):

        guildOwnerId = ctx.guild.owner_id
        currentUserId = ctx.author.id
        guildID = ctx.guild.id

        # if it is not the guild owner ignore | only guild owner can set threshold
        if currentUserId == guildOwnerId:

            try:
                # in case the user has put in words as a digit instead of actual integers
                newThresholdCounter = int(total)

                self.dataBase.setServerThreshold(guildID, newThresholdCounter)

                await ctx.channel.send(f"New message threshold has been set for the server to {newThresholdCounter:0,}")

            except ValueError:
                pass

    # would be used if hosting bot yourself
    def scanCurrentServer(self):

        # scanning al the guild the bot is currently in and return their ID
        for guild in self.bot.guilds:
            self.dataBase.addNewGuild(guild)

    # this is only for debugging not to be used for implementation
    @commands.command()
    async def setstreak(self, ctx, amount):

        guildMessageFrom = str(ctx.guild.id)

        testGuildID = 602439523284287508

        if ctx.author.id == 125604422007914497 and ctx.guild.id == testGuildID:

            mentionedUser = ctx.message.mentions[0].name
            mentionedUserID = ctx.message.mentions[0].id
            # give the user a streak point
            self.dataBase.setStreakToUser(testGuildID, mentionedUserID, int(amount))

            await ctx.channel.send(f"{mentionedUser} streak point has been set to {amount} ")

    # this is only for debugging not to be used for implementation
    @commands.command()
    async def setmsg(self, ctx, amount):

        guildMessageFrom = str(ctx.guild.id)
        testGuildID = 602439523284287508
        if ctx.author.id == 125604422007914497 and ctx.guild.id == testGuildID:
            mentionedUser = ctx.message.mentions[0].name
            mentionedUserID = str(ctx.message.mentions[0].id)
            # give the user a streak point
            self.dataBase.setMsgCountToUser(testGuildID, mentionedUserID, int(amount))

            await ctx.channel.send(f"{mentionedUser} MSG point has been set to {amount} ")


if __name__ == "__main__":
    bot.add_cog(StreakBot(bot))
    bot.remove_command("help")
    bot.run("")

"""
Methods to update when changing Json

when guild joins
when user join guilds

"""
