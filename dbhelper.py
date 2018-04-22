import sqlite3


class DBHelper:
    def __init__(self, dbname="userdata.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup(self):
        tbluser = "CREATE TABLE IF NOT EXISTS users (userID varchar(20), locationLAT decimal(9,6), locationLONG " \
                  "decimal(9,6), cityName varchar(20), lang varchar(10), notPeriod int) "
        self.conn.execute(tbluser)
        self.conn.commit()

    def add_user(self, userID, locationLAT, locationLONG, lang):
        stmt = "INSERT INTO users (userID, locationLAT, locationLONG, lang) SELECT (?), (?), (?), (?) WHERE NOT EXISTS(SELECT 1 FROM users WHERE userID = (?))"
        args = (userID, locationLAT, locationLONG, lang, userID)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_user_with_cityName(self, userID, locationLAT, locationLONG, cityname, lang):
        stmt = "INSERT INTO users (userID, locationLAT, locationLONG, cityName, lang) SELECT (?), (?), (?), (?), (?) WHERE NOT EXISTS(SELECT 1 FROM users WHERE userID = (?))"
        args = (userID, locationLAT, locationLONG, cityname, lang, userID)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_user(self, userID):
        stmt = "DELETE FROM users WHERE userID = (?)"
        args = (userID, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def update_user_location(self, userID, locationLAT, locationLONG):
        stmt = "UPDATE users SET locationLAT = (?), locationLONG = (?) WHERE userID = (?)"
        args = (locationLAT, locationLONG, userID)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def update_user_location_with_cityName(self, userID, locationLAT, locationLONG, cityName):
        stmt = "UPDATE users SET locationLAT = (?), locationLONG = (?), cityName = (?)  WHERE userID = (?)"
        args = (locationLAT, locationLONG, cityName, userID)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def update_user_notification_rate(self, userID, notPeriod):
        stmt = "UPDATE users SET notPeriod = (?) WHERE userID = (?)"
        args = (notPeriod, userID)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_user_cityName(self, userID):
        stmt = "SELECT cityName FROM users WHERE userID = (?)"
        args = (userID, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_user_long(self, userID):
        stmt = "SELECT locationLONG FROM users WHERE userID = (?)"
        args = (userID, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_user_lat(self, userID):
        stmt = "SELECT locationLAT FROM users WHERE userID = (?)"
        args = (userID, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_user_notPeriod(self, userID):
        stmt = "SELECT notPeriod FROM users WHERE userID = (?)"
        args = (userID, )
        return self.conn.execute(stmt, args)

    def get_city_lng(self, cityname):
        stmt = "SELECT lng FROM pk_il WHERE il_adi = (?) COLLATE NOCASE"
        args = (cityname,)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_city_lat(self, cityname):
        stmt = "SELECT lat FROM pk_il WHERE il_adi = (?) COLLATE NOCASE"
        args = (cityname,)
        return [x[0] for x in self.conn.execute(stmt, args)]
