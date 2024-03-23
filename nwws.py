import logging
import sys
import signal
import slixmpp
import ssl
import yaml
from xml.dom import minidom

with open('config.yml', 'r') as file:
    nwwsConfig = yaml.safe_load(file)

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
        content = itemlist[0].firstChild.nodeValue
        if cccc == 'KMPX':
            print('INFO\t message stanza rcvd from nwws-oi saying... ' + msg['body'])
            print('TTAAII: '+ttaaii)
            print('cccc: '+cccc)
            print('awipsid: '+awipsid)
            print('id: '+id)
            filename = 'output/'+str(id)+'.'+str(awipsid)+'.xml'
            with open(filename, "w") as f:
                f.write(str(msg))


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    jid = nwwsConfig['username']+'@'+nwwsConfig['domain']+'/'+nwwsConfig['resource']
    room = nwwsConfig['room']+'@'+nwwsConfig['conferenceServer']
    xmpp = nwwsBot(jid, nwwsConfig['password'], room, nwwsConfig['nickname'])
    xmpp.connect()
    xmpp.process(forever=False)