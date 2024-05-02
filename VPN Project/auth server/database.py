import sqlite3 as lite

class Clients:

    def __init__(self) -> None:
        # Connect to users database
        self.__users = lite.connect('users.db')

    def __create_table(self):

        c = self.__users.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users
                  (
                  email text primary key,
                  password text,
                  addr text
                  )""")
        self.__users.commit()
        c.close()

    def add_user(self, data):
        pass

    def get_users(self, data):
        pass

    def login(self, data):
        pass



class Proxies:
    
    def __init__(self) -> None:
        # Connect to proxies database
        self.__proxies = lite.connect('proxis.db')

    def __create_table(self):
        c = self.__proxies.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS proxies
                  (
                  email text primary key,
                  password text,
                  addr text,
                  locked int,
                  active int
                  )""")
        
        c.execute("""UPDATE proxies SET active=0 WHERE active==1 """)
        
        self.__proxies.commit()
        c.close()
        

    def get_active_proxies(self):
        c = self.__proxies.cursor()

        c.execute("""SELECT host, port FROM Proxies WHERE active=1""")

    def update_active_proxy(self, data):
        pass

    def add_proxy(self, data):
        pass

    def remove_proxy(self, data):
        pass

