import logging
import sys
import signal
import slixmpp
import ssl
import yaml
from xml.dom import minidom
import sqlite3

with open('config.yml', 'r') as file:
    nwwsConfig = yaml.safe_load(file)

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

database = 'nwws.db'

# create a database connection
conn = create_connection(database)

def signal_handler(signal, frame):
    print('Caught Ctrl+C. Exiting.')
    xmpp.disconnect()
    print('Disconnected')
    #sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class nwwsBot(slixmpp.ClientXMPP):

    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # XMPP Ping

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("groupchat_message", self.muc_message)

        self.room = room
        self.nick = nick

        # nwws-oi.weather.gov requires TLSv2.3
        self.ssl_version = ssl.PROTOCOL_SSLv23

    async def session_start(self, event):
        self.send_presence()
        self.get_roster()
        self.plugin['xep_0045'].join_muc(self.room,
                                         self.nick,
                                         # If a room password is needed, use:
                                         # password=the_room_password,
                                         )

    def muc_message(self, msg):
        print('INFO\t message stanza rcvd from nwws-oi saying... ' + msg['body'])
        xmldoc = minidom.parseString(str(msg))
        itemlist = xmldoc.getElementsByTagName('x')
        ttaaii = itemlist[0].attributes['ttaaii'].value
        cccc = itemlist[0].attributes['cccc'].value
        awipsid = itemlist[0].attributes['awipsid'].value
        id = itemlist[0].attributes['id'].value
        issued = itemlist[0].attributes['issue'].value
        content = itemlist[0].firstChild.nodeValue
        sql = ''' INSERT OR IGNORE INTO cccc(cccc) VALUES(?) '''
        cur = conn.cursor()
        cur.execute(sql, (cccc,))
        conn.commit()
        if cccc == 'KMPX' or cccc == 'KWNS' or cccc == 'KDLH' or cccc == 'KARX' or cccc == 'KFGF' or cccc =='KFSD' or cccc == 'KABR' or cccc == 'KMSR':
            sql = ''' INSERT INTO products(cccc,ttaaii,awipsid,nwsid,body,contents) VALUES(?,?,?,?,?,?) '''
            cur = conn.cursor()
            cur.execute(sql, (cccc,ttaaii,awipsid,id,msg['body'],content))
            conn.commit()

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


if __name__ == '__main__':

    sql_create_cccc_table = """ CREATE TABLE IF NOT EXISTS cccc (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        cccc text NOT NULL,
                                        UNIQUE(cccc)
                                    ); """
    
    sql_create_products_table = """ CREATE TABLE IF NOT EXISTS products (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        cccc text,
                                        ttaaii text,
                                        awipsid text,
                                        nwsid text,
                                        body text,
                                        contents text
                                    ); """

    # create tables
    if conn is not None:
        # create cccc table
        create_table(conn, sql_create_cccc_table)

        # create mpx table
        create_table(conn, sql_create_products_table)
    else:
        print("Error! cannot create the database connection.")

    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    jid = nwwsConfig['username']+'@'+nwwsConfig['domain']+'/'+nwwsConfig['resource']
    room = nwwsConfig['room']+'@'+nwwsConfig['conferenceServer']
    xmpp = nwwsBot(jid, nwwsConfig['password'], room, nwwsConfig['nickname'])
    xmpp.connect()
    xmpp.process(forever=False)