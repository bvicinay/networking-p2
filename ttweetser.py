import socket
import sys
from thread import *
import threading
import traceback

connectUserFlag = 'user'
tweetFlag = 'twee'
subscribeFlag = "subs"
unsubscribeFlag = "unsu"
timelineFlag = "time"
exitFlag = "exit"

args = sys.argv
if len(args) < 2:
    print("Please specify the port number")
    sys.exit()

port = int(sys.argv[1])

class Tweet:
  def __init__(self, text, hashtags, owner):
    self.text = text
    self.hashtags = hashtags
    self.owner = owner

class User:
  def __init__(self, username):
    self.username = username
    self.hashtags = []
    self.lastSeen = 0
    self.subscribedToAll = False

    def subscribe(self, hashtag):
        if len(self.hashtags) >= 3:
            return True
        if hashtag == "ALL":
            self.subscribedToAll = True
            return True
        if hashtag in self.hashtags:
            return True
        else:
            self.hashtags.append(hashtag)
            return True
    
    def unsubscribe(self, hashtag):
        if hashtag == "ALL":
            self.subscribedToAll = False
            return True
        if hashtag in self.hashtags:
            self.hashtags.remove(hashtag)
            return True
       return False



def sendMessage(conn, msg):
    if len(msg) >= 999:
        conn.sendall(bytes(msg))
        return True
    size = str(len(msg))
    size = "0"*(3-len(size)) + size
    conn.sendall(bytes(size + msg))

def checkUser(user):
    return user in users.keys()

def threadExecute(c):
    try:
        loggedUser = None
        sendMessage(c, "hello my name is borja")
        state = "standby"
        command = ""
        length = ""
        while True:
            if state == "standby":
                header = c.recv(7).decode("utf-8")
                length = int(header[:3])
                command = header[3:7]
                state = command
                sendMessage(c, "hello")

            if state == connectUserFlag:
                data = c.recv(length).decode("utf-8")
                user = str(data).strip()
                if checkUser(user):
                    sendMessage(c, "true")
                    state = "exit"
                else:
                    sendMessage(c, "fail")
                    users[loggedUser] = User(loggedUser)
                    state = "standby"

            if state == tweetFlag:
                data = c.recv(length).decode("utf-8")
                parts = data.split('+++')
                tweetText = parts[0].decode("utf-8")
                hashtags=parts[1].split("#")[1:]
                global_tweets.append(Tweet(tweetText, hashtags, loggedUser))
                state = "standby"

            elif state == subscribeFlag:
                data = c.recv(length).decode("utf-8")
                if loggedUser.subscribe(data):
                    sendMessage(c, "true")
                else: 
                    sendMessage(c, "fail")
                state = "standby"

            elif state == unsubscribeFlag:
                data = c.recv(length).decode("utf-8")
                loggedUser.unsubscribe(data):

                state = "standby"
                
            elif state == timelineFlag:
                newTweets  = global_tweets[loggedUser.lastSeen:]
                loggedUser.lastseen = len(global_tweets)
                buffer = ""
                for tweet in newTweets:
                    subscribed = False
                    originHashtag = None
                    for h in tweet.hashtags:
                        if (h in loggedUser.hashtags) or loggedUser.subscribedToAll:
                            subscribed = True
                            originHashtag = h
                            break
                    if not subscribed:
                        continue
                    buffer += "{} {}: {} {}".format(loggedUser.username, tweet.owner, tweet.text, originHashtag)
                    sendMessage(c, "wait" + str(len(buffer)))
                    sendMessage(c, buffer)
                    state = "standby"
                    
            elif state == exitFlag:
                c.close()
                loggedUser = None
    except (Exception):
        traceback.print_exc()
        thread_lock.release() 
        allowNew = True
        print("Disconnected from client, killing thread..")

thread_lock = threading.Lock() 

connections = [] ## (conn, addr, thread)
threads = []
users = {}
global_tweets = []
global_hashtags = {}
allowNew = True

print("Starting Server..")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", port))
s.listen(1)

while True:
    if allowNew:
        print("Listening on port " + str(port))
        conn, addr = s.accept()
        connections.append((conn, addr))
        newThread = thread_lock.acquire()
        threads.append(newThread)
        print("New client connection established from " + str(addr[1]) + " on port " + str(addr[0]))
        
        start_new_thread(threadExecute, (conn,))
        if len(connections) >= 5:
            print("Connection maximum reached, blocking new requests until a client disconnects.")
            allowNew = False
        