import sqlite3
import json
import time
from datetime import datetime
start = time.time()


class DataBase(sqlite3.Connection):

    today = datetime.today().date().strftime("%d-%m-%Y")


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
                    active_voice Integer ,
                    no_active_voice Integer ,
                    total_voice_time Integer,
                    track_voice Integer,
                    voice_threshold Integer,
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
                    UNIQUE (userID)

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

    # to be used for debugging only
    def setStreakToUser(self, serverID, userID, amount):
        # give the user a streak, set the streaked to True, set the highest streak if if it's greater than current streak

        userInfo = {'userID': userID, 'serverID': serverID, 'amount': amount}

        self.cursor.execute('''UPDATE server SET streakCounter = :amount, streaked = 1
                    WHERE userID = :userID AND serverID = :serverID ;
                    ''', userInfo)

        self.cursor.execute('''UPDATE server SET highestStreak = CASE WHEN streakCounter >= highestStreak THEN 
                streakCounter ELSE highestStreak END  WHERE userID = :userID AND serverID = :serverID ''',
                            userInfo)

        self.commit()

    # to be used for debugging only
    def setMsgCountToUser(self, serverID, userID, amount):
        # give the user a streak, set the streaked to True, set the highest streak if if it's greater than current streak

        userInfo = {'userID': userID, 'serverID': serverID, 'amount': amount}

        self.cursor.execute('''UPDATE server SET highMsgCount = :amount
                       WHERE userID = :userID AND serverID = :serverID ;
                       ''', userInfo)

        self.commit()

    def addGlobalStreakUser(self, userID, streakDay):

        userInfo = {'userID': userID, 'lastStreakDay': streakDay}
        self.cursor.execute('''UPDATE global SET streakCounter = streakCounter + 1, streaked = 1, lastStreakDay = :lastStreakDay
                            WHERE userID = :userID;
                            ''', userInfo)

        self.cursor.execute('''UPDATE global SET highestStreak = CASE WHEN streakCounter >= highestStreak THEN 
                streakCounter ELSE highestStreak END  WHERE userID = :userID ''',
                            userInfo)

        self.commit()

    def checkUserStreaked(self, serverID, userID):
        # check if the user has streaked
        self.cursor.execute('SELECT streaked FROM server WHERE serverID = :serverID AND userID = :userID ;',
                            {'userID': userID, 'serverID': serverID})
        return self.cursor.fetchone()[0]

    def checkUserGlobalStreaked(self, userID):
        # check if the user has streaked
        self.cursor.execute('SELECT streaked FROM global WHERE userID = :userID ;',
                            {'userID': userID})
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

        self.cursor.execute(
            'UPDATE global SET serverName =:serverName WHERE serverID = :serverID; ',
            {'serverID': server.id, 'serverName': server.name})

        self.commit()

    def updateUserName(self, user):
        self.cursor.execute(
            'UPDATE server SET userName =:userName WHERE userID =:userID; ',
            {'userID': user.id, 'userName': f"{user.name}#{user.discriminator}"})
        self.cursor.execute(
            'UPDATE global SET userName =:userName WHERE userID =:userID; ',
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

        userInfo = {'userID': userID, 'serverID': serverID, 'msgCount': msgCount}
        self.cursor.execute(
            'UPDATE server SET msgCount = msgCount + :msgCount, highMsgCount = highMsgCount + :msgCount WHERE serverID = :serverID AND userID = :userID; ',
            userInfo)

        self.cursor.execute(
            'UPDATE global SET msgCount = msgCount + :msgCount, highMsgCount = highMsgCount + :msgCount WHERE userID = :userID; ',
            userInfo)

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

    def getGlobalThreshold(self):
        self.cursor.execute('SELECT serverThreshold Threshold FROM global',
                            )
        return self.cursor.fetchone()[0]

    def getMessageCount(self, serverID, userID):
        # retrieve the amount of message the user current has now
        self.cursor.execute('SELECT msgCount FROM server WHERE serverID = :serverID AND userID = :userID ;',
                            {'userID': userID, 'serverID': serverID})
        # retrieve message count
        return self.cursor.fetchone()[0]

    def getMessageCountGlobal(self, userID):
        # retrieve the amount of message the user current has now
        self.cursor.execute('SELECT msgCount FROM global WHERE userID = :userID ;',
                            {'userID': userID})
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
        ORDER BY  streakCounter DESC, msgCount DESC, userName ASC
        LIMIT 25''')
        return self.cursor.fetchall()

    def addUser(self, server, user):
        # add user to the database
        # add singular user to the database
        # get the server's threshold
        self.cursor.execute('SELECT serverThreshold,voice_threshold, track_voice FROM server WHERE serverID = ?', (server.id,))

        serverThreshold, voice_threshold, track_voice = self.cursor.fetchone()


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
            'highMsgCount': 0,
            'active_voice':0,
            'no_active_voice':0,
            'total_voice_time':0,
            'track_voice':track_voice, 
            'voice_threshold':voice_threshold}

        self.cursor.execute('''INSERT OR IGNORE INTO server(serverName, serverID, userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount, active_voice,no_active_voice,
        total_voice_time, track_voice, voice_threshold)
                VALUES (:serverName,:serverID,:userName, :userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount, :active_voice,:no_active_voice,
                :total_voice_time, :track_voice, :voice_threshold)''',
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

    def add_user_global(self, server, user):
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
                    'highMsgCount': 0,
                    'active_voice': 0,
                    'no_active_voice': 0,
                    'total_voice_time': 0,
                    'track_voice': 1,
                    'voice_threshold':7200}

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

                self.cursor.execute('''INSERT OR IGNORE INTO server(serverName, serverID, userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount, active_voice,no_active_voice,
                              total_voice_time, track_voice, voice_threshold)
                                      VALUES (:serverName,:serverID,:userName, :userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount, :active_voice,:no_active_voice,
                                      :total_voice_time, :track_voice,:voice_threshold )''',
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
            'lastStreakDay': "Never Streaked",
            'highMsgCount': 0}

        self.cursor.execute('''INSERT OR IGNORE INTO  global (serverName, serverID,userName, userID, serverThreshold,msgCount,streakCounter, streaked, highestStreak, lastStreakDay, highMsgCount)
                                                VALUES (:serverName,:serverID, :userName,:userID, :serverThreshold,:msgCount,:streakCounter, :streaked, :highestStreak, :lastStreakDay, :highMsgCount)''',
                            userInfoGlobal
                            )

    def setNewDayStats(self):

        self.cursor.execute(
            'UPDATE server SET msgCount = 0, streaked = 0, streakCounter = CASE WHEN  streaked = 0 THEN 0 ELSE streakCounter END,total_voice_time = 0, active_voice = 0; ')
        self.cursor.execute(
            'UPDATE global SET msgCount = 0, streaked = 0, streakCounter = CASE WHEN msgCount < serverThreshold THEN 0 ELSE streakCounter END')
        self.commit()

    def add_voice_column(self):
        self.cursor.execute('''ALTER TABLE server ADD COLUMN  active_voice Integer ;''')
        self.cursor.execute('''ALTER TABLE server ADD COLUMN  no_active_voice Integer  ;''')
        self.cursor.execute('''ALTER TABLE server ADD COLUMN  total_voice_time Integer;''')
        self.cursor.execute('''ALTER TABLE server ADD COLUMN  track_voice Integer;''')
        self.cursor.execute('''ALTER TABLE server ADD COLUMN  voice_threshold Integer;''')
        self.commit()

    def set_voice_join_time(self, server, user):
        data = {'time': int(time.time()),
                'server_id': server.id,
                'user_id': user.id}

        self.cursor.execute('UPDATE server set active_voice =:time WHERE userID = :user_id AND serverID =:server_id;',
                            data)

        self.commit()

    def update_voice_time(self, server, user):
        data = {'time': int(time.time()),
                'server_id': server.id,
                'user_id': user.id,
                'date': self.today,
                }

        self.cursor.execute(
            'UPDATE server SET no_active_voice =:time WHERE userID = :user_id AND serverID =:server_id;',
            data)

        # will be used to calculate how long the user has been in call and not muted
        self.cursor.execute(
            '''UPDATE server SET total_voice_time =(no_active_voice-active_voice)+total_voice_time, no_active_voice =0,active_voice=0
            WHERE userID = :user_id AND serverID =:server_id;''',
            data)

        self.cursor.execute('''UPDATE server SET 
                streaked = CASE WHEN total_voice_time >= voice_threshold THEN 1  ELSE 0 END
             WHERE userID = :user_id AND serverID =:server_id;
        ''', data)

        self.cursor.execute('''UPDATE server SET
        lastStreakDay = CASE WHEN streaked = 1 THEN :date ELSE lastStreakDay END
             WHERE userID = :user_id AND serverID =:server_id;

        ''', data)

        self.commit()

    def track_voice(self, server):

        data = {'server_id': server.id}

        self.cursor.execute('''SELECT track_voice FROM server WHERE serverID = :server_id''', data)

        return self.cursor.fetchone()[0]

    def enable_track_voice(self, server):

        data = {'server_id': server.id}

        self.cursor.execute(
            '''UPDATE server SET track_voice = 1 WHERE serverID = :server_id;''',
            data)

        self.commit()

    def disable_track_voice(self, server):

        data = {'server_id': server.id}

        self.cursor.execute(
            '''UPDATE server SET track_voice = 0 WHERE serverID = :server_id;''',
            data)

        self.commit()

    def get_user_voice_time(self, server, user):
        data = {'server_id': server.id,
                'user_id': user.id
                }
        self.cursor.execute('''SELECT total_voice_time FROM server WHERE serverID = :server_id AND userID =:user_id;''',
                            data)

        return self.cursor.fetchone()[0]

    def get_voice_guild_threshold(self, server):
        data = {'server_id': server.id,
                }
        self.cursor.execute('''SELECT voice_threshold FROM server WHERE serverID = :server_id;''', data)

        return self.cursor.fetchone()[0]

    def set_voice_guild_threshold(self, server, amount):
        data = {'server_id': server.id,
                'amount': amount}

        # set default to 7200 if there's threshold set for the server
        self.cursor.execute(
            '''UPDATE server SET voice_threshold =:amount WHERE serverID = :server_id;''',
            data)

        self.commit()

    def set_default_voice_values(self):
        self.cursor.execute(
            '''UPDATE server SET voice_threshold = 7200, track_voice = 1,active_voice = 0, no_active_voice = 0, 
             total_voice_time = 0''')

        self.commit()


    def get_voice_status(self, server, user):
        data = {'server_id': server.id, 'user_id': user.id
                }
        self.cursor.execute('''SELECT active_voice FROM server WHERE serverID = :server_id AND userID = :user_id;''',
                            data)

        return self.cursor.fetchone()[0]



    def get_current_voice_total(self, server, user):
        data = {'server_id': server.id, 'user_id': user.id
                }
        self.cursor.execute(
            '''SELECT total_voice_time FROM server WHERE serverID = :server_id AND userID = :user_id;''',
            data)

        return self.cursor.fetchone()[0]
