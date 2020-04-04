import discord
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime
from database import DataBase
import dbl

from discord.ext.commands import CommandError

bot = commands.Bot(command_prefix='.')


class StreakBot(commands.Cog, command_attrs=dict(hidden=False, brief="Normal User", help="I'm a mysterious command.")):
    today = datetime.today().date().strftime("%d-%m-%Y")
    yesterday = None

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")
        self.embed = None
        self.token = ""
        self.dblpy = dbl.DBLClient(self.bot, self.token,
                                   autopost=True)  # Auto post will post your guild count every 30 minutes

        self.dataBase = DataBase('discordStreakBot.db')
        #
        # self.dataBase.createTable()
        # self.dataBase.createGlobalTable()
        # self.dataBase.add_voice_column()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}\n')
        self.dateCheck.start()
        # self.scanCurrentServer()

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     if isinstance(error, CommandError):
    #         return
    #     raise error

    async def on_guild_post(self):
        print("Server count posted successfully")

    @commands.Cog.listener()
    async def on_voice_state_update(self, user, previous_voice_state, current_voice_state):

        user = user
        guild = user.guild

        # check if the guild wants to track
        if self.dataBase.track_voice(guild):

            # check if the user has already streaked other wise ignore
            if not self.dataBase.checkUserStreaked(guild.id, user.id):

                # if the user just recently joined a voice channel
                joined_a_voice_channel = True if previous_voice_state.channel is None else False
                user_left_voice_channel = True if current_voice_state.channel is None else False
                user_current_mute_state = True if current_voice_state.mute or current_voice_state.self_mute else False

                # if the user is not muted prior to joining voice call or current state
                if not user_current_mute_state and joined_a_voice_channel:
                    print("user has joined a voice channel")
                    self.dataBase.set_voice_join_time(guild, user)

                elif user_left_voice_channel and user_current_mute_state:
                    print("user has left voice channel while muted")

                elif user_left_voice_channel and not user_current_mute_state:
                    self.dataBase.update_voice_time(guild, user)
                    print("user has left voice channel")

                elif user_current_mute_state and joined_a_voice_channel:
                    print("user has joined the channel while muted")

                elif user_current_mute_state:
                    print("user is muted ")
                    self.dataBase.update_voice_time(guild, user)

                elif not user_current_mute_state:
                    print("user has un-muted")
                    self.dataBase.set_voice_join_time(guild, user)


    @commands.command(brief="Admin", help="``!voice enable enable`` Enable voice to be counted for streaking\n"
                                          "``!voice disable`` Disable voice to be counted for streaking\n"
                                          "``!voice threshold (amount) optional:(minute|hour)``\n"
                                          "Set the threshold for how long the user needs to be in call to gain a streak"
                                          "user's that are muted will not be counted to words tracking total time they were in the call")
    async def voice(self, ctx, *args):

        if len(args) <= 4:

            guild = ctx.author.guild

            command = ' '.join(args)

            if command == "enable":

                # check if the guild command has already been enabled otherwise enable it
                if not self.dataBase.track_voice(guild):
                    self.dataBase.enable_track_voice(guild)
                    await ctx.channel.send("Voice channels will now be counted for streak!", delete_after=10)

                else:
                    await ctx.channel.send("Voice channels are already counted for streak!", delete_after=10)

            # check if the guild command was already disabled other wise enable it
            elif command == "disable":
                if self.dataBase.track_voice(guild):
                    self.dataBase.disable_track_voice(guild)
                    await ctx.channel.send("Voice channels will not be counted for streak!", delete_after=10)
                else:
                    await ctx.channel.send("Voice channels are already disabled for streak!", delete_after=10)

            # will be used to track the
            elif 'threshold' in command:

                # unpack the threshold amount to be set
                command, threshold_amount, *other_arguments = args

                # try convert the given digit into
                try:
                    threshold_amount = int(threshold_amount)

                except ValueError:

                    await ctx.channel.send("Invalid digit sent")

                # if no other arguments were passed in (minutes | hours)
                if not other_arguments:

                    self.dataBase.set_voice_guild_threshold(guild, threshold_amount)

                    await ctx.channel.send(
                        f"New voice threshold has been set to {threshold_amount:0,} seconds for {guild.name}\n",
                        delete_after=10)

                # if the user has given minutes argument convert it to seconds then update database
                elif other_arguments[0].startswith('minute'):

                    convert_threshold_amount = threshold_amount * 60

                    self.dataBase.set_voice_guild_threshold(guild, convert_threshold_amount)

                    await ctx.channel.send(
                        f"New voice threshold has been set to {threshold_amount:0,} minute for {guild.name}\n",
                        delete_after=10)

                # if the user has given hour argument convert it to seconds then update database
                elif other_arguments[0].startswith('hour'):

                    convert_threshold_amount = (threshold_amount * 60) * 60

                    self.dataBase.set_voice_guild_threshold(guild, convert_threshold_amount)

                    await ctx.channel.send(
                        f"New voice threshold has been set to {threshold_amount:0,} hour for {guild.name}\n",
                        delete_after=10)

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
            try:
                streakedGlobal = self.dataBase.checkUserGlobalStreaked(userID)
            except TypeError:
                # will be used if the user does not exist in the global leaderboard by accident
                self.dataBase.add_user_global(guild, user)
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

    @commands.command(
        help="``!streak (Optional:me|global|@someone) ``: A very wide-purpose command, with the arguments basically self-explanatory. If you want to view the global leaderboard, use no arguments.")
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

            usersTotalMessages = '\n'.join([f'{user[4]:0,}' for user in leaderBoard])
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

        usersTotalMessages = '\n'.join([f'{user[4]:0,}' for user in leaderBoard])
        usersStreakDays = '\n'.join([str(user[5]) for user in leaderBoard])

        self.embed = dict(
            title=f"**==GLOBAL STREAK LEADERBOARD==**",
            color=9127187,
            thumbnail={
                "url": "https://cdn4.iconfinder.com/data/icons/miscellaneous-icons-2-1/200/misc_movie_leaderboards3-512.png"},
            fields=[dict(name="**Users**", value=userNames, inline=True),
                    dict(name="Streak Total", value=usersStreakDays, inline=True),
                    dict(name="Words Sent Today", value=usersTotalMessages, inline=True)],
            footer=dict(text=f"Total Words counted on {self.today} | Threshold for Global is 500 word Count")
        )
        await ctx.channel.send(embed=discord.Embed.from_dict(self.embed))

    # checking for the dates if its a new day
    @tasks.loop(minutes=5)
    async def dateCheck(self):

        currentDay = datetime.today().date().strftime("%d-%m-%Y")

        if self.today != currentDay:
            # keeping tracking of the day  before
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

    @commands.command(help="``!info``: View basic bot information, like user count, server count, latency, etc.")
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
            description=f":white_small_square: Minimum word count for streak is {guildThreshold:0,}.\n"
                        f":white_small_square: Streaks are added when you reach {guildThreshold:0,} words or more.\n"
                        ":white_small_square: Streak will reset at midnight GMT failure to meet word count.\n",
            thumbnail={"url": "https://cdn3.iconfinder.com/data/icons/shopping-e-commerce-33/980/shopping-24-512.png"},
            fields=[dict(name=f"**====================** \n", value=f":book: Total Servers\n"
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
                               f":white_small_square: [support channel](https://discord.gg/F6hvm2) for features request| upcoming updates",
                         inline=False),

                    dict(name="**Update**",
                         value=f":white_small_square: **!help** display help command for the bot\n"
                               f":white_small_square: **!streak global** NEW COMMAND SEE GLOBAL LEADERBOARD\n"
                               f":white_small_square: **!streak @someone** to view their summary profile\n"
                               f":white_small_square: **!streak me** to view your own profile \n"
                               f":white_small_square: small Achievement has been added summary profile.\n"
                               f":white_small_square: set threshold for amount words for a streak **!threshold amount** \n",
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

        achievementStreakCheck = '\n'.join(
            [f":gem: {milestone} Streaks" if userStreak >= milestone else f":x: {milestone} Streaks" for milestone in
             milestones])

        achievementMsgCheck = '\n'.join([
            f":gem: {milestone:02,} words" if totalMessage >= milestone else f":x: {milestone:02,} words"
            for milestone in msgMilestone])

        # add the achievement to the embed to display
        achievements = dict(name="**Streak Milestones**",
                            value=f"{achievementStreakCheck}", inline=True)

        achievement2 = dict(name="**Total Words Milestones**",
                            value=f"{achievementMsgCheck}", inline=True)

        bottomBar = dict(name="=====**More Achievements To Come**====", value=f"\u200b")

        self.embed['fields'].append(achievements)
        self.embed['fields'].append(achievement2)
        self.embed['fields'].append(bottomBar)

    @commands.command(brief="Admin",
                      help="``!threshold (amount)``: Set the minimum number of words for a server member to get a streak.")
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
    @commands.command(hidden=True)
    async def setstreak(self, ctx, amount):

        testGuildID = 602439523284287508

        if ctx.author.id == 125604422007914497 and ctx.guild.id == testGuildID:
            mentionedUser = ctx.message.mentions[0].name
            mentionedUserID = ctx.message.mentions[0].id
            # give the user a streak point
            self.dataBase.setStreakToUser(testGuildID, mentionedUserID, int(amount))

            await ctx.channel.send(f"{mentionedUser} streak point has been set to {amount} ")

    @commands.command(help="``!help (optional: (category name|command name)``: What do you think I do?")
    async def help(self, ctx, *args):

        if not args:
            # getting list of commands and putting speech bubble over them to make them stand out
            list_of_commands = ','.join(map(lambda word: f'`{word}`', command_event.command_categories))

            embed = dict(
                title=f"**==DISCORD STREAK HELP==**",
                color=9127187,
                thumbnail={
                    "url": "https://cdn0.iconfinder.com/data/icons/small-n-flat/24/678110-sign-info-512.png"},
                fields=[
                    dict(name="**Categories**",
                         value=f"{list_of_commands}",
                         inline=False),

                    dict(name="**Basic Info**",
                         value="To view the commands in each category, do ``!help <category name>``.\n"
                               "To view the help for each command, do ``!help <command name>``.\n",
                         inline=False),

                    dict(name="**Support Channel**",
                         value=f"[Support channel](https://discord.gg/F6hvm2)\n===**You Can**===\n"
                               f":white_small_square: Features request\n"
                               f":white_small_square: Upcoming updates\n"
                               f":white_small_square: Report a bug\n"
                               f":white_small_square: Many more things to  come!\n", inline=False),

                    dict(name="**Other Information**",
                         value=f":white_small_square: [Vote on top.gg](https://top.gg/bot/685559923450445887) \n"
                               f":white_small_square: bots.ondiscord.xyz [pending review]",
                         inline=False),

                ],

                footer=dict(text="We hope you find everything OK!"),

            )

            await ctx.channel.send(embed=discord.Embed.from_dict(embed))
            # no need to go next step
            return

        # if the length of command sent by user is less than 3 (3 is a place holder and can be grown
        if len(args) <= 3:

            command = ' '.join(args).title()

            if command in command_event.command_categories:

                # get list of commands and jon them
                list_of_commands = ' '.join(command_event.command_categories.get(command))

                embed = dict(
                    title=f"**==DISCORD STREAK HELP==**",
                    color=9127187,
                    thumbnail={
                        "url": "https://cdn0.iconfinder.com/data/icons/small-n-flat/24/678110-sign-info-512.png"},
                    fields=[
                        dict(name="**Commands**",
                             value=f"{list_of_commands}",
                             inline=False),
                    ],
                    footer=dict(text="We hope you find everything OK!"),
                )
                await ctx.channel.send(embed=discord.Embed.from_dict(embed))

            elif command.lower() in command_event.commands:

                command_help_info = command_event.commands.get(command.lower())

                embed = dict(
                    title=f"**==DISCORD STREAK HELP==**",
                    color=9127187,
                    thumbnail={
                        "url": "https://cdn0.iconfinder.com/data/icons/small-n-flat/24/678110-sign-info-512.png"},
                    fields=[
                        dict(name="**Commands**", value=f"{command_help_info}",
                             inline=False),
                    ],
                    footer=dict(text="We hope you find everything OK!"),
                )
                await ctx.channel.send(embed=discord.Embed.from_dict(embed))

            else:

                await ctx.channel.send("That command or category doesn't exist!")

    # this is only for debugging not to be used for implementation
    @commands.command(hidden=True)
    async def setmsg(self, ctx, amount):

        testGuildID = 602439523284287508
        if ctx.author.id == 125604422007914497 and ctx.guild.id == testGuildID:
            mentionedUser = ctx.message.mentions[0].name
            mentionedUserID = str(ctx.message.mentions[0].id)
            # give the user a streak point
            self.dataBase.setMsgCountToUser(testGuildID, mentionedUserID, int(amount))

            await ctx.channel.send(f"{mentionedUser} MSG point has been set to {amount} ")


class CommandEvent:

    def __init__(self):
        self.command_categories = {}
        self.commands = {}
        self.set_up_commands()

    def set_up_commands(self):

        # loop through the commands
        for command in bot.get_cog('StreakBot').get_commands():

            # ignore all hidden commands
            if not command.hidden:
                # get the category name
                command_category = command.brief

                # add the commands to the command list dictionary
                self.commands[command.name] = command.help

                # check if a key already exist for this category
                if self.command_categories.get(command.brief) is None:

                    self.command_categories[command_category] = [f"`{command.name}`"]

                else:
                    # otherwise append to an existing key
                    self.command_categories[command_category].append(f"`{command.name}`")


if __name__ == "__main__":
    bot.add_cog(StreakBot(bot))
    command_event = CommandEvent()
    bot.run("")

"""
Methods to update when changing Json

when guild joins
when user join guilds

"""
