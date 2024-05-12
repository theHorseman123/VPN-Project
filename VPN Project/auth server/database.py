import sqlite3 as lite

class Clients:

    def __init__(self) -> None:
        # Connect to users database
        self.__users = lite.connect('./auth server/users.db')

    def __create_table(self):
        
        try:
            cursor = self.__users.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS users
                    (
                    user text primary key,
                    password text,
                    active int
                    )""")
            
            cursor.execute("""UPDATE users SET active=0 WHERE active=1""")

            self.__users.commit()
            cursor.close()
        except lite.Error:
            print("datbase error: %s" % str(lite.Error))

    def add_user(self, data):
        try:
            cursor = self.__users.cursor()
            cursor.execute("""INSERT INTO users user, password, active VALUES(?, ? ,?, 1)""", (data[0], data[1]))
            cursor.commit()
        except lite.Error:
            print("datbase error: %s" % str(lite.Error))
            return "database error"
        return "pass"

    def get_users(self, data):
        try:
            cursor = self.__users.cursor()
            cursor.execute("SELECT user, addr FROM users WHERE 1=1")
            rows = cursor.fetchall()
        except lite.Error:
            print("datbase error: %s" % str(lite.Error))
            return "database error"
        return rows

    def login(self, data):
        try:
            cursor = self.__users.cursor()
            cursor.execute("""SELECT user FROM users WHERE user=? AND password=?""")
        except:
            pass



class Proxies:
    
    def __init__(self) -> None:
        # Connect to proxies database
        self.__proxies = lite.connect('./auth server/proxies.db')

    def __create_table(self):
        cursor = self.__proxies.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS proxies
                  (
                  user text primary key
                  password text,
                  addr text,
                  locked int,
                  key text,
                  active int
                  )""")
        
        cursor.execute("""UPDATE proxies SET active=0 WHERE active=1 """)
        
        self.__proxies.commit()
        cursor.close()
        

    def get_active_proxies(self):
        cursor = self.__proxies.cursor()

        cursor.execute("""SELECT addr, locked FROM proxies WHERE active=1""")

        proxies = cursor.fetchall()
        cursor.close()

        return proxies

    def update_active_proxy(self, data):
        cursor = self.__proxies.cursor()
        cursor.execute("""SELECT locked FROM proxies WHERE user=? AND password=?""")
        if cursor.fetchall() == None:
            cursor.close()
            return "an error occured"
        
        if len(data) == 3: # update activity
            cursor.execute("""UPDATE proxies SET addr=?, active=1 WHERE user=?""", (data[2], data[0]))
            cursor.commit()
            cursor.close()

            return "pass"
        if len(data) == 4: # update proxie lock code
            cursor.execute("""UPDATE proxies SET code=? locked=1 WHERE user=?""", (data[2], data[0]))
            cursor.commit()
            cursor.close()
            
            return "pass"
        
    def add_proxy(self, data):
        try:
            cursor = self.__proxies.cursor()
            if len(data) == 3:
                cursor.execute("""INSERT INTO proxies user, password, addr VALUES(?, ?, ?)""", (data[0], data[1], data[2]))
            elif len(data) == 4:
                cursor.execute("""INSERT INTO proxies user, password, addr, locked, code VALUES(?, ?, ?, 1, ?)""", (data[0], data[1], data[2], data[3]))
            
            cursor.commit()
            
        except lite.Error as error:
            print(f"Error in database: {str(error)}")
            cursor.close()
            return "an error occured"
        
        cursor.close()
        return "pass"

    def remove_proxy(self, user):
        try:
            # TODO: make it much more secured, maybe with encryption
            cursor = self.__proxies.cursor()
            cursor.execute("""DELETE FROM proxies WHERE user=?""", (user, ))
        except lite.error as error:
            print(f"Error in database: {str(error)}")
            cursor.close()
            return "an error occured"
        
        cursor.close()
        return "pass"

