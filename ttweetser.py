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
        self.lastSeen = 0 ##TODO: only show tweets sent after subscribed
        self.subscribedToAll = False

    def subscribe(self, hashtag):
        if len(self.hashtags) >= 3:
            return False
        if hashtag == "ALL":
            self.hashtags.append(hashtag)
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
            print("Unsubscribed user from " + hashtag)
            return True
        print("Could not unsubscribe user, not subscribed")
        return False



def sendMessage(conn, msg, addNumbers = True):
    if not addNumbers:
        conn.sendall(bytes(msg))
        return True
    size = str(len(msg[4:]))
    size = "0"*(3-len(size)) + size
    conn.sendall(bytes(size + msg))

def checkUser(user):
    return user in users.keys()

def threadExecute(c):
    try:
        loggedUser = None
        
        state = "standby"
        command = ""
        length = ""
        while True:
            if state == "standby":
                header = str(c.recv(7).decode("utf-8"))
                print("---receivedHeader:" + str(header))
                if len(str(header).strip()) > 0:
                    length = int(header[:3])
                    command = header[3:7]
                    state = command
                

            if state == connectUserFlag:
                data = str(c.recv(length).decode("utf-8"))
                print("---received:" + str(data))
                user = str(data).strip()
                if user in connectedUsers:
                    sendMessage(c, "fail")
                    state = "exit"
                elif user in users.keys():
                    sendMessage(c, "true")
                    loggedUser = users[user]
                    state = "standby"
                    connectedUsers.add(loggedUser)
                    print("User {} logged in succesfully".format(user))
                else:
                    sendMessage(c, "true")
                    users[user] = User(user)
                    loggedUser = users[user]
                    state = "standby"
                    connectedUsers.add(loggedUser)
                    print("User {} logged in succesfully".format(user))

                

            if state == tweetFlag:
                data = str(c.recv(length).decode("utf-8"))
                print("---received:" + str(data))
                parts = data.split('+++')
                tweetText = parts[0].decode("utf-8")
                hashtags=parts[1].split("#")[1:]
                hashtags[-1] = hashtags[-1].strip()
                global_tweets.append(Tweet(tweetText, hashtags, loggedUser))
                state = "standby"
                print("Received tweet from {}: {} - hashtags: {}".format(loggedUser.username, tweetText, str(hashtags)))

            elif state == subscribeFlag:
                data = str(c.recv(length).decode("utf-8"))[1:].strip()
                print("---received:" + str(data))
                if loggedUser.subscribe(str(data)):
                    sendMessage(c, "true")
                    print("Subscribed {} to {} succesfully".format(loggedUser.username, str(data)))
                else: 
                    sendMessage(c, "fail")
                    print("Could not subscribe {} to {}".format(loggedUser.username, str(data)))
                
                state = "standby"

            elif state == unsubscribeFlag:
                data = str(c.recv(length).decode("utf-8"))[1:]
                print("---received:" + str(data))
                loggedUser.unsubscribe(data)

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
                    buffer += "+++{} {}: {} {}".format(loggedUser.username, tweet.owner.username, tweet.text, "#" + originHashtag)
                sendMessage(c, "wait" + str(len(buffer)), True)
                sendMessage(c, buffer, False)
                state = "standby"
                
            elif state == exitFlag:
                print("Received exit signal. Closing connection...")
                c.close()
                loggedUser = None
                break
                state = "standby"

    except (Exception):
        traceback.print_exc()
        thread_lock.release() 
        allowNew = True
        print("Disconnected from client, killing thread..")

thread_lock = threading.Lock() 

connections = [] ## (conn, addr, thread)
connectedUsers = set()
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
        print("New client connection established from " + str(addr[0]) + " on port " + str(addr[1]))
        
        start_new_thread(threadExecute, (conn,))
        if len(connections) >= 5:
            print("Connection maximum reached, blocking new requests until a client disconnects.")
            allowNew = False
        