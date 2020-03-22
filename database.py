import sqlite3
import json
import time

start = time.time()


class DataBase(sqlite3.Connection):

    def __init__(self, dataBasePath):
        sqlite3.Connection.__init__(self, dataBasePath)
        self.cursor = self.cursor()

    def createTable(self, tableName):
        self.cursor.execute(f"""CREATE TABLE {tableName} (
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
                streakCounter END  WHERE userID = :userID AND serverID = :serverID ''',
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

    def addMessageCount(self, serverID, userID, msgCount):
        # add message count the users have sent
        self.cursor.execute(
            'UPDATE server SET msgCount = msgCount + :msgCount, highMsgCount = highMsgCount + :msgCount WHERE serverID = :serverID AND userID = :userID; ',
            {'userID': userID, 'serverID': serverID, 'msgCount': msgCount})

        self.commit()

        # retrieve the amount of message the user current has now
        self.cursor.execute('SELECT msgCount FROM server WHERE serverID = :serverID AND userID = :userID ;',
                            {'userID': userID, 'serverID': serverID})

        return self.cursor.fetchone()[0]

    def serverThreshold(self, serverID, thresholdAmount):
        self.cursor.execute(' UPDATE server SET serverThreshold = :threshAmount WHERE serverID = :serverID ;',
                            {'serverID': serverID, 'thresholdAmount': thresholdAmount})

    def removeServer(self, serverID):
        # remove the server from the database
        self.cursor.execute('DELETE FROM server WHERE serverID = :serverID ', {'serverID': serverID})
        self.commit()

    def removeUserFromServer(self, serverID, userID):
        self.cursor.execute('DELETE FROM server WHERE serverID = :serverID AND userID = :userID',
                            {'serverID': serverID, 'userID': userID})
        self.commit()

    def addUser(self, server, user):
        # add user to the database
        # add singular user to the database
        # get the server's threshold
        self.cursor.execute('SELECT serverThreshold FROM server WHERE serverID = ?', (serverID,))
        serverThreshold = self.cursor.fetchone()[0]
        userInfo = {
            'serverID': server.id,
            'serverName': server.name,
            'userName': user.name
            'userID': user.id,
            'msgCount': 0,
            'serverThreshold': serverThreshold,
            'streakCounter': 0,
            'streaked': 0,
            'highestStreak': 0,
            'lastStreakDay': "Never Streaked",
            'highMsgCount': 0}

        self.cursor.execute('''INSERT OR IGNORE INTO server(serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                VALUES (:serverName,:serverID,userName, :userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                            userInfo
                            )
        self.commit()

    def addNewGuildUsers(self, server, users):
        # looping through the list of users that get passed on
        # will  be used when a guild joins
        for user in users:
            userInfo = {
                'serverID': server.id,
                'serverName': server.name,
                'userName': user.name,
                'userID': user.id,
                'msgCount': 0,
                'serverThreshold': 100,
                'streakCounter': 0,
                'streaked': 0,
                'highestStreak': 0,
                'lastStreakDay': "Never Streaked",
                'highMsgCount': 0}

            self.cursor.execute('''INSERT OR IGNORE INTO server(serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                            VALUES (:serverName,:serverID, :userName,:userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                                userInfo
                                )
            self.commit()
print("commit test")
