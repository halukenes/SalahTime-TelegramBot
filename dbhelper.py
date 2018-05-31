import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import urllib.parse as urlparse


class DBHelper:
    def __init__(self, dbname="userdata.sqlite"):
        self.dbname = dbname
        url = urlparse.urlparse("postgres://fkdlunsaopdbwe"
                                ":d1ec6d177e3ef65b05c0a0ecc3961db45134149eaa91d6a8438aa1f163affa9d@ec2-54-228-181-43"
                                ".eu-west-1.compute.amazonaws.com:5432/d1vck26bn55skn")
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor()
        print("Connected to Heroku Postgre")

    def setup(self):
        tblusers = "CREATE TABLE IF NOT EXISTS users (userID varchar(20), locationLAT decimal(9,6), locationLONG " \
                  "decimal(9,6), gmt int, cityName varchar(20), lang varchar(10), notPeriod int, nextnotTime varchar(" \
                  "20), remindCode varchar(20), interactionCount int, reminderCount int, readsuraCount int);"
        tblsuras = "CREATE TABLE IF NOT EXISTS suras (suraID SERIAL PRIMARY KEY, suraName varchar(20), readCount int);"
        self.cur.execute(tblusers)
        self.cur.execute(tblsuras)

    def add_user(self, userID, locationLAT, locationLONG, lang, gmt):
        stmt = "INSERT INTO users (userID, locationLAT, locationLONG, lang) SELECT %s, %s, %s, %s WHERE NOT EXISTS(SELECT %s FROM users WHERE userID::int = %s);"
        args = (userID, locationLAT, locationLONG,lang, userID, userID, )
        self.cur.execute(stmt, args)

    def add_user_with_language(self, userID, lang):
        stmt = "INSERT INTO users (userID, lang, interactionCount, reminderCount, readsuraCount, stage) SELECT %s, %s, %s, %s, %s, %s WHERE NOT EXISTS (SELECT userID FROM users WHERE userID::int = %s);"
        args = (userID, lang, 0, 0, 0, 0, userID, )
        self.cur.execute(stmt, args)

    def add_user_with_cityName(self, userID, locationLAT, locationLONG, cityname, lang, gmt):
        stmt = "INSERT INTO users (userID, locationLAT, locationLONG, gmt, cityName, lang) SELECT %s, %s, %s, %s, %s, %s WHERE NOT EXISTS(SELECT %s FROM users WHERE userID::int = %s);"
        args = (userID, locationLAT, locationLONG, gmt, cityname, lang, userID, userID, )
        self.cur.execute(stmt, args)

    def delete_user(self, userID):
        stmt = "DELETE FROM users WHERE userID::int = %s;"
        args = (userID,)
        self.cur.execute(stmt, args)

    def update_user_location(self, userID, locationLAT, locationLONG):
        stmt = "UPDATE users SET locationLAT = %s, locationLONG = %s WHERE userID::int = %s;"
        args = (locationLAT, locationLONG, userID, )
        self.cur.execute(stmt, args)

    def update_user_location_and_gmt(self, userID, locationLAT, locationLONG, cityName, gmt):
        stmt = "UPDATE users SET locationLAT = %s, locationLONG = %s, cityName = %s, gmt = %s WHERE userID::int = %s;"
        args = (locationLAT, locationLONG, cityName, gmt, userID, )
        self.cur.execute(stmt, args)

    def update_user_language(self, userID, lang):
        stmt = "UPDATE users SET lang = %s WHERE userID::int = %s;"
        args = (lang, userID, )
        self.cur.execute(stmt, args)

    def update_user_location_with_cityName(self, userID, locationLAT, locationLONG, cityName, gmt):
        stmt = "UPDATE users SET locationLAT = %s, locationLONG = %s, cityName = %s, gmt = %s WHERE userID::int = %s"
        args = (locationLAT, locationLONG, cityName, gmt, userID, )
        self.cur.execute(stmt, args)

    def update_user_notification_rate(self, userID, notPeriod):
        stmt = "UPDATE users SET notPeriod = %s WHERE userID::int = %s;"
        args = (notPeriod, userID, )
        self.cur.execute(stmt, args)

    def update_user_nextnotTime(self, userID, time):
        stmt = "UPDATE users SET nextnotTime = %s WHERE userID::int = %s;"
        args = (time, userID, )
        self.cur.execute(stmt, args)

    def get_user_language(self, userID):
        stmt = "SELECT lang FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[2:-3]
        return row

    def get_user_cityName(self, userID):
        stmt = "SELECT cityName FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[2:-3]
        return row

    def get_user_long(self, userID):
        stmt = "SELECT locationLONG FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        rows = str(self.cur.fetchone())[10:-4]
        return rows

    def get_user_lat(self, userID):
        stmt = "SELECT locationLAT FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[10:-4]
        return row

    def get_user_notPeriod(self, userID):
        stmt = "SELECT notPeriod FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[1:-2]
        return row

    def get_users_to_notify(self, time):
        stmt = "SELECT userID FROM users WHERE nextnotTime::varchar = '"+str(time)+"';"
        self.cur.execute(stmt)
        row = self.cur.fetchall()
        return row

    def get_gmt(self, userID):
        stmt = "SELECT gmt FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[1:-2]
        return row

    def get_remindCode(self, userID):
        stmt = "SELECT remindCode FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[1:-2]
        return row

    def get_stage(self, userID):
        stmt = "SELECT stage FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[1:-2]
        return int(row)

    def get_pS(self, userID):
        stmt = "SELECT pres FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[2:-3]
        return row

    def get_pM(self, userID):
        stmt = "SELECT prem FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[2:-3]
        return row

    def get_pL(self, userID):
        stmt = "SELECT prel FROM users WHERE userID::int = "+str(userID)+";"
        self.cur.execute(stmt)
        row = str(self.cur.fetchone())[2:-3]
        return row

    def update_sura(self, suraName):
        stmt = "UPDATE suras SET readcount = readcount + 1 WHERE suraname = %s; INSERT INTO suras (suraname, readcount) SELECT %s, %s WHERE NOT EXISTS (SELECT suraname FROM suras WHERE suraname = %s);"
        args = (suraName, suraName, "1", suraName)
        self.cur.execute(stmt, args)

    def update_user_interaction(self, userID):
        stmt = "UPDATE users SET interactionCount = interactionCount + 1 WHERE userID::int = %s;"
        args = (userID, )
        self.cur.execute(stmt, args)

    def update_user_reminderCount(self, userID):
        stmt = "UPDATE users SET reminderCount = reminderCount + 1 WHERE userID::int = %s;"
        args = (userID, )
        self.cur.execute(stmt, args)

    def update_user_readsuraCount(self, userID):
        stmt = "UPDATE users SET readsuraCount = readsuraCount + 1 WHERE userID::int = %s;"
        args = (userID, )
        self.cur.execute(stmt, args)

    def update_user_remindCode(self, userID, remindCode):
        stmt = "UPDATE users SET remindCode = %s WHERE userid::int = %s;"
        args = (remindCode, userID, )
        self.cur.execute(stmt, args)

    def update_user_stage(self, userID, stage):
        stmt = "UPDATE users SET stage = %s WHERE userid::int = %s;"
        args = (stage, userID, )
        self.cur.execute(stmt, args)

    def update_user_pS(self, userID, pS):
        stmt = "UPDATE users SET pres = %s WHERE userid::int = %s;"
        args = (pS, userID, )
        self.cur.execute(stmt, args)

    def update_user_pM(self, userID, pM):
        stmt = "UPDATE users SET prem = %s WHERE userid::int = %s;"
        args = (pM, userID, )
        self.cur.execute(stmt, args)

    def update_user_pL(self, userID, pL):
        stmt = "UPDATE users SET prel = %s WHERE userid::int = %s;"
        args = (pL, userID, )
        self.cur.execute(stmt, args)

