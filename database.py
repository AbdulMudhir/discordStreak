import sqlite3
import json
import time

start = time.time()


class DataBase(sqlite3.Connection):

    def __init__(self, dataBasePath):
        sqlite3.Connection.__init__(self, dataBasePath)
        self.cursor = self.cursor()

    def createTable(self):

        self.cursor.execute(f"""CREATE TABLE server (
                    serverID INTEGER,
                    serverName TEXT,
                    serverThreshold INTEGER,
                    serverChannels TEXT,
                    userName TEXT,
                    userID INTEGER,
                    msgCount INTEGER,
                    streakCounter INTEGER,
                    streaked INTEGER,
                    highestStreak INTEGER,
                    lastStreakDay TEXT,
                    highMsgCount INTEGER,
                    UNIQUE (userID, serverID)

                )
        """)

    def createGlobalTable(self):

        self.cursor.execute(f"""CREATE TABLE global (
                    serverID INTEGER,
                    serverName TEXT,
                    serverThreshold INTEGER,
                    serverChannels TEXT,
                    userName TEXT,
                    userID INTEGER,
                    msgCount INTEGER,
                    streakCounter INTEGER,
                    streaked INTEGER,
                    highestStreak INTEGER,
                    lastStreakDay TEXT,
                    highMsgCount INTEGER,
                    UNIQUE (userID, serverID)

                )
                """)

    def addStreakToUser(self, serverID, userID, streakDay):
        # give the user a streak, set the streaked to True, set the highest streak if if it's greater than current streak

        userInfo = {'userID': userID, 'serverID': serverID, 'lastStreakDay': streakDay}

        self.cursor.execute('''UPDATE server SET streakCounter = streakCounter + 1, streaked = 1, lastStreakDay = :lastStreakDay
                    WHERE userID = :userID AND serverID = :serverID ;
                    ''', userInfo)

        self.cursor.execute('''UPDATE server SET highestStreak = CASE WHEN streakCounter >= highestStreak THEN 
                streakCounter ELSE highestStreak END  WHERE userID = :userID AND serverID = :serverID ''',
                            userInfo)

        self.commit()

    def checkUserStreaked(self, serverID, userID):
        # check if the user has streaked
        self.cursor.execute('SELECT streaked FROM server WHERE serverID = :serverID AND userID = :userID ;',
                            {'userID': userID, 'serverID': serverID})
        return self.cursor.fetchone()[0]

    def checkUserHighestMsgCount(self, serverID, userID):
        # retrieve user highest message count
        self.cursor.execute('SELECT highMsgCount FROM server WHERE serverID = :serverID AND userID = :userID ;',
                            {'userID': userID, 'serverID': serverID})
        return self.cursor.fetchone()[0]

    def updateServerName(self, server):
        self.cursor.execute(
            'UPDATE server SET serverName =:serverName WHERE serverID = :serverID; ',
            {'serverID': server.id, 'serverName': server.name})
        self.commit()

    def updateUserName(self, user):
        self.cursor.execute(
            'UPDATE server SET userName =:userName WHERE userID =:userID; ',
            {'userID': user.id, 'userName': f"{user.name}#{user.discriminator}"})
        self.commit()

    def getServerName(self, server):
        self.cursor.execute('SELECT serverName FROM server WHERE serverID = :serverID ;',
                            {'serverID': server.id})
        return self.cursor.fetchone()[0]

    def getUserName(self, user):
        self.cursor.execute('SELECT userName FROM server WHERE userID = :userID ;',
                            {'userID': user.id})
        return self.cursor.fetchone()[0]

    def addMessageCount(self, serverID, userID, msgCount):
        # add message count the users have sent
        self.cursor.execute(
            'UPDATE server SET msgCount = msgCount + :msgCount, highMsgCount = highMsgCount + :msgCount WHERE serverID = :serverID AND userID = :userID; ',
            {'userID': userID, 'serverID': serverID, 'msgCount': msgCount})

        self.commit()

    def getUserInfo(self, serverID, userID):
        self.cursor.execute(
            '''SELECT userName,msgCount,streakCounter, streaked, highestStreak, lastStreakDay,highMsgCount
            FROM server WHERE serverID = :serverID AND userID = :userID ''', {'serverID': serverID, 'userID': userID})

        return self.cursor.fetchone()

    def getServerThreshold(self, serverID):
        self.cursor.execute('SELECT serverThreshold FROM server WHERE serverID = :serverID ;',
                            {'serverID': serverID})
        return self.cursor.fetchone()[0]

    def getMessageCount(self, serverID, userID):
        # retrieve the amount of message the user current has now
        self.cursor.execute('SELECT msgCount FROM server WHERE serverID = :serverID AND userID = :userID ;',
                            {'userID': userID, 'serverID': serverID})
        # retrieve message count
        return self.cursor.fetchone()[0]

    def setServerThreshold(self, serverID, thresholdAmount):
        self.cursor.execute(' UPDATE server SET serverThreshold = :thresholdAmount WHERE serverID = :serverID ;',
                            {'serverID': serverID, 'thresholdAmount': thresholdAmount})

        self.commit()

    def removeServer(self, serverID):
        # remove the server from the database
        self.cursor.execute('DELETE FROM server WHERE serverID = :serverID ', {'serverID': serverID})
        self.cursor.execute('DELETE FROM global WHERE serverID = :serverID ', {'serverID': serverID})
        self.commit()

    def removeUser(self, serverID, userID):
        self.cursor.execute('DELETE FROM server WHERE serverID = :serverID AND userID = :userID',
                            {'serverID': serverID, 'userID': userID})

        self.cursor.execute('DELETE FROM global WHERE serverID = :serverID AND userID = :userID',
                            {'serverID': serverID, 'userID': userID})
        self.commit()

    def addUserName(self, serverID, user):
        self.cursor.execute(' UPDATE server SET userName = :userName WHERE serverID = :serverID AND userID = :userID;',
                            {'serverID': serverID, 'userID': user.id, 'userName': f"{user.name}#{user.discriminator}"})

        self.commit()

    def viewServerLeaderBoard(self, serverID):
        self.cursor.execute('''SELECT serverID, serverName, userName,userID,msgCount,streakCounter FROM server 
        WHERE serverID =?
        ORDER BY streakCounter DESC, userName ASC
        LIMIT 25''', (serverID,))
        return self.cursor.fetchall()

    def viewGlobalLeaderBoard(self):
        self.cursor.execute('''SELECT  serverID, serverName, userName,userID,msgCount,streakCounter FROM global 
        ORDER BY streakCounter DESC, userName ASC
        LIMIT 25''')
        return self.cursor.fetchall()

    def addUser(self, server, user):
        # add user to the database
        # add singular user to the database
        # get the server's threshold
        self.cursor.execute('SELECT serverThreshold FROM server WHERE serverID = ?', (server.id,))
        serverThreshold = self.cursor.fetchone()[0]
        userInfo = {
            'serverID': server.id,
            'serverName': server.name,
            'userName': f"{user.name}#{user.discriminator}",
            'userID': user.id,
            'msgCount': 0,
            'serverThreshold': serverThreshold,
            'streakCounter': 0,
            'streaked': 0,
            'highestStreak': 0,
            'lastStreakDay': "Never Streaked",
            'highMsgCount': 0}

        self.cursor.execute('''INSERT OR IGNORE INTO server(serverName, serverID, userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                VALUES (:serverName,:serverID,:userName, :userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                            userInfo
                            )
        userInfoGlobal = {
            'serverID': server.id,
            'serverName': server.name,
            'userName': f"{user.name}#{user.discriminator}",
            'userID': user.id,
            'msgCount': 0,
            'serverThreshold': 500,
            'streakCounter': 0,
            'streaked': 0,
            'highestStreak': 0,
            'lastStreakDay': "Never Streaked",
            'highMsgCount': 0}

        self.cursor.execute('''INSERT OR IGNORE INTO global(serverName, serverID, userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                        VALUES (:serverName,:serverID,:userName, :userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                            userInfoGlobal
                            )
        self.commit()

    def addNewGuild(self, server):
        # looping through the list of users that get passed on
        # will  be used when a guild joins
        for user in server.members:
            # if the user is not  a bot
            if not user.bot:
                userInfo = {
                    'serverID': server.id,
                    'serverName': server.name,
                    'userName': f"{user.name}#{user.discriminator}",
                    'userID': user.id,
                    'msgCount': 0,
                    'serverThreshold': 100,
                    'streakCounter': 0,
                    'streaked': 0,
                    'highestStreak': 0,
                    'lastStreakDay': "Never Streaked",
                    'highMsgCount': 0}

                userInfoGlobal = {
                    'serverID': server.id,
                    'serverName': server.name,
                    'userName': f"{user.name}#{user.discriminator}",
                    'userID': user.id,
                    'msgCount': 0,
                    'serverThreshold': 500,
                    'streakCounter': 0,
                    'streaked': 0,
                    'highestStreak': 0,
                    'lastStreakDay': "Never Streaked",
                    'highMsgCount': 0}

                self.cursor.execute('''INSERT OR IGNORE INTO server(serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                                VALUES (:serverName,:serverID, :userName,:userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                                    userInfo
                                    )
                self.cursor.execute('''INSERT OR IGNORE INTO global(serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                                                VALUES (:serverName,:serverID, :userName,:userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                                    userInfoGlobal
                                    )
                self.commit()

    def addJsonGuildToSQL(self, guildID, guildThreshold, userID, msgCount, streakCounter, streaked, highestStreak,
                          lastStreakDay, highestMsgCount):
        userInfo = {
            'serverID': guildID,
            'serverName': None,
            'userName': None,
            'userID': userID,
            'msgCount': msgCount,
            'serverThreshold': guildThreshold,
            'streakCounter': streakCounter,
            'streaked': streaked,
            'highestStreak': highestStreak,
            'lastStreakDay': lastStreakDay,
            'highMsgCount': highestMsgCount}

        self.cursor.execute('''INSERT OR IGNORE INTO server (serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                                        VALUES (:serverName,:serverID, :userName,:userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                            userInfo
                            )

        userInfoGlobal = {
            'serverID': guildID,
            'serverName': None,
            'userName': None,
            'userID': userID,
            'msgCount': 0,
            'serverThreshold': 500,
            'streakCounter': 0,
            'streaked': 0,
            'highestStreak': 0,
            'lastStreakDay': 0,
            'highMsgCount': 0}

        self.cursor.execute('''INSERT OR IGNORE INTO  global (serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                                                VALUES (:serverName,:serverID, :userName,:userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                            userInfoGlobal
                            )

    def setNewDayStats(self):
        print("i am here 3")
        self.cursor.execute(
            'UPDATE server SET msgCount = 0, streaked = 0, streakCounter = CASE WHEN msgCount < serverThreshold THEN 0 ELSE streakCounter END')
        self.commit()
