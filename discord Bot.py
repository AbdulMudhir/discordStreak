import discord
import json
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime
import time

bot = commands.Bot(command_prefix='!')

usersInCurrentGuild = {}

streakData = json.load(open("streak.json", "r+"))


class StreakBot(commands.Cog):
    today = datetime.today().date().strftime("%d-%m-%Y")
    yesterday = None

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}\n')
        self.dateCheck.start()

        # scanning al the guild the bot is currently in and return their ID
        for guild in self.bot.guilds:

            # create a list to hold each users for different guild
            usersInCurrentGuild[guild.id] = {}

            for member in guild.members:

                # checking if the user is a bot as we wont be tracking the bots
                if not member.bot:
                    # add those users into the system
                    # each member has total message, days of streak
                    usersInCurrentGuild[guild.id].update({member.id: [0, 0]})
                else:
                    continue

        json.dump(usersInCurrentGuild, open("streak.json", "w"))

    @commands.Cog.listener()
    async def on_message(self, message):
        user = message.author
        userId = str(message.author.id)
        messageLength = len(message.content.split())
        guildMessageFrom = str(message.guild.id)

        # adding total total messages to the user
        if not user.bot:
            streakData[guildMessageFrom][userId][0] += messageLength

    # streak commands
    @commands.command()
    async def streak(self, ctx):

        # getting the guild the message was sent from
        guildMessageFrom = str(ctx.guild.id)

        # retrieving the data for that guild
        streakUsersFromGuild = streakData[guildMessageFrom]

        # obtain the users from that specific guilkd
        usersID = streakUsersFromGuild.keys()

        # unpack the total messages, and streak days
        totalMessages, streakDays = list(zip(*streakUsersFromGuild.values()))

        # sorting the users based on the highest streak (will be changing to streak days)
        streakDays, usersID, totalMessages, = zip(*sorted(zip(streakDays, usersID, totalMessages, ), reverse=True))

        # converting the id to their Original Names
        userNames = "__\n__".join([self.bot.get_user(int(user)).name for user in usersID][0:25])

        # creating a String containing all the total messages
        usersTotalMessages = "\n".join([str(total) for total in  totalMessages][0:25])

        # creating a String containing all the streaks
        usersStreakDays = "\n".join([str(streak) for streak in streakDays][0:25])

        embed = dict(
            title=f"**==STREAK LEADERBOARD==**",
            color=9127187,
            thumbnail={
                "url": "https://cdn4.iconfinder.com/data/icons/miscellaneous-icons-2-1/200/misc_movie_leaderboards3-512.png"},
            fields=[dict(name="**Users**", value=userNames, inline=True),
                    dict(name="Streak Days", value=usersStreakDays, inline=True),
                    dict(name="Total Messages Sent", value=usersTotalMessages, inline=True)],
            footer=dict(text=f"Total Messages counted on {self.today}")
        )
        await ctx.channel.send(embed=discord.Embed.from_dict(embed))

    # checking for the dates if its a new day
    @tasks.loop(seconds=600)
    async def dateCheck(self):

        currentDay = datetime.today().date().strftime("%d-%m-%Y")

        if self.today != currentDay:
            # keeping tracking of the day  before
            yesterday = self.today
            # updating today so it is the correct date
            self.today = currentDay

            print("New Day")
            time.sleep(5)
            self.addStreaks()

    @staticmethod
    def addStreaks():

        # we will be looping through the servers to add or reset the streak
        for guild in streakData:

            # check each members in th eguild
            for member in streakData[guild]:

                # retrieve total messages sent
                memberTotalMessage = streakData[guild][member][0]

                # if the user has sent more than 20 words today
                if memberTotalMessage >= 20:

                    # reset their messages sent
                    streakData[guild][member][0] = 0

                    # add a streak
                    streakData[guild][member][1] += 1

                else:
                    # reset their messages sent
                    streakData[guild][member][0] = 0

                    # clear the streak if they had any
                    streakData[guild][member][1] = 0

        # back up the file
        json.dump(streakData, open("streak.json", "w"))

    @commands.Cog.listener()
    async def on_member_join(self, member):

        guildMemberJoined = str(member.guild.id)

        print(f"New user has joined {member.guild.name}")

        # add the user to the correct server
        if not member.bot:
            streakData[guildMemberJoined].update({str(member.id): [0, 0]})

        json.dump(streakData, open("streak.json", "w"))



    @commands.Cog.listener()
    async def on_member_remove(self, member):

        guildMemberJoined = str(member.guild.id)

        print(f"user has left  {member.guild.name}")

        # remove the user from data as they have left
        if not member.bot:
            streakData[guildMemberJoined].pop(str(member.id))

        json.dump(streakData, open("streak.json", "w"))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        print("New Guild Has Joined")

        guildId = str(guild.id)

        streakData.update({guildId: {}})

        for member in guild.members:
            # checking if the user is a bot as we wont be tracking the bots
            if not member.bot:
                # add those users into the system
                # each member has total message, days of streak
                streakData[guildId].update({str(member.id): [0, 0]})
            else:
                continue

        json.dump(streakData, open("streak.json", "w"))


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        print(f"A Guild Has left {guild.name}")

        guildId = str(guild.id)

        # remove the server from data
        streakData.pop(guildId)

        # update the data
        json.dump(streakData, open("streak.json", "w"))


if __name__ == "__main__":
    bot.add_cog(StreakBot(bot))

    bot.run("")
