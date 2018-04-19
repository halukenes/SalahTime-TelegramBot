import sqlite3


class DBHelper:
    def __init__(self, dbname="userdata.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup(self):
        tbluser = "CREATE TABLE IF NOT EXISTS users (userID varchar(20), locationLAT decimal(9,6), locationLONG " \
                  "decimal(9,6), lang varchar(10), notPeriod int) "
        self.conn.execute(tbluser)
        self.conn.commit()

    def add_user(self, userID, locationLAT, locationLONG, lang):
        stmt = "INSERT INTO users (userID, locationLAT, locationLONG, lang) VALUES (?, ?, ?, ?)"
        args = (userID, locationLAT, locationLONG, lang)
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

    def update_user_notification_rate(self, userID, notPeriod):
        stmt = "UPDATE users SET notPeriod = (?) WHERE userID = (?)"
        args = (notPeriod, userID)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_user_long(self, userID):
        stmt = "SELECT locationLONG FROM items WHERE userID = (?)"
        args = (userID, )
        return self.conn.execute(stmt, args)

    def get_user_lat(self, userID):
        stmt = "SELECT locationLAT FROM items WHERE userID = (?)"
        args = (userID, )
        return self.conn.execute(stmt, args)

    def get_user_notPeriod(self, userID):
        stmt = "SELECT notPeriod FROM items WHERE userID = (?)"
        args = (userID, )
        return self.conn.execute(stmt, args)
