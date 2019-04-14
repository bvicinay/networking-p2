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
    ## A class representing a Tweet
    currNumber = 0

    def __init__(self, text, hashtags, owner):
        self.text = text
        self.hashtags = hashtags
        self.owner = owner
        self.time = Tweet.currNumber
        Tweet.currNumber += 1

class User:
    ## A class representing a user
    def __init__(self, username):
        self.username = username
        self.hashtags = []
        self.lastSeen = 0 
        self.subscribedToAll = False
        self.subscriptions = {}

    def subscribe(self, hashtag):
        if len(self.hashtags) >= 3: ## cannot be subscribed to more than 3 hashtags
            return False
        if hashtag in self.hashtags:
            return True
        
        self.hashtags.append(hashtag)
        if hashtag == "ALL": 
            self.subscribedToAll = True
        
        self.subscriptions[hashtag] = Tweet.currNumber ## account for subscribing after a tweet is sent on that hashtag
        return True

    def unsubscribe(self, hashtag):
        if hashtag == "ALL":
            self.subscribedToAll = False
            return True
        if hashtag in self.hashtags:
            self.hashtags.remove(hashtag) ##Unsubscribe user from hashtag
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
    ## The connection on a separate thread, handles all commands for a specific user
    try:
        loggedUser = None
        
        state = "standby"
        command = ""
        length = ""
        while True:
            if state == "standby":
                ##thread_lock.release() 
                header = str(c.recv(7).decode("utf-8"))
                ##print("---receivedHeader:" + str(header))
                if len(str(header).strip()) > 0:
                    length = int(header[:3])
                    command = header[3:7]
                    state = command
                else:
                    raise Exception
                

            if state == connectUserFlag:
                ## Setups the connection for the user
                data = str(c.recv(length).decode("utf-8"))
                ##print("---received:" + str(data))
                user = str(data).strip()
                if user in connectedUsers: ##user logged in alaready
                    print("User logged in already")
                    sendMessage(c, "fail")
                    state = "exit"
                elif len(connectedUsers) >= 5: ##cannot have more than 5 concurrent connections
                    print("Parallel connections limit exceeded, dropping new user")
                    sendMessage(c, "fail")
                    state = "exit"
                elif user in users.keys(): #chack if user exists and load its data, else create new user
                    sendMessage(c, "true")
                    loggedUser = users[user]
                    state = "standby"
                    connectedUsers.add(loggedUser.username)
                    print("User {} logged in succesfully".format(user))
                else:
                    sendMessage(c, "true")
                    users[user] = User(user)
                    loggedUser = users[user]
                    state = "standby"
                    connectedUsers.add(loggedUser.username)
                    print("User {} logged in succesfully".format(user))

                

            if state == tweetFlag: 
                ## state associated with receiving and processing a tweet
                data = str(c.recv(length).decode("utf-8"))
                #print("---received:" + str(data))
                parts = data.split('+++') # separate the different fields
                tweetText = parts[0].decode("utf-8")
                hashtags=parts[1].split("#")[1:]
                hashtags[-1] = hashtags[-1].strip()
                global_tweets.append(Tweet(tweetText, hashtags, loggedUser)) ## Add tweet to the global data
                state = "standby"
                print("Received tweet from {}: {} - hashtags: {}".format(loggedUser.username, tweetText, str(hashtags)))

            elif state == subscribeFlag:
                ## subscribe to a tweet if not subscribed already
                data = str(c.recv(length).decode("utf-8"))[1:].strip()
                #print("---received:" + str(data))
                if loggedUser.subscribe(str(data)): ## check if subscription was succesful, error handling
                    sendMessage(c, "true")
                    print("Subscribed {} to {} succesfully".format(loggedUser.username, str(data)))
                else: 
                    sendMessage(c, "fail")
                    print("Could not subscribe {} to {}".format(loggedUser.username, str(data)))
                
                state = "standby"

            elif state == unsubscribeFlag: ##unsubscribe user from hashtag
                data = str(c.recv(length).decode("utf-8"))[1:]
                print("---received:" + str(data))
                loggedUser.unsubscribe(data)

                state = "standby"
                
            elif state == timelineFlag:
                ## send the timeline of corresponding tweets to the user
                newTweets  = global_tweets[loggedUser.lastSeen:]
                loggedUser.lastSeen = len(global_tweets)
                buffer = ""
                for tweet in newTweets:
                    subscribed = False
                    originHashtag = None
                    for h in tweet.hashtags:
                        if (h in loggedUser.hashtags) or loggedUser.subscribedToAll and tweet.time >= loggedUser.subscriptions[h]:
                            ## checked if user is subscribed to the hashtag, subscribed to all and make sure he subscribed before the tweet was sent
                            subscribed = True
                            originHashtag = h
                            break
                    if not subscribed:
                        continue
                    ## accumulate tweets for sending them all at the same time.
                    buffer += "+++{} {}: {} {}".format(loggedUser.username, tweet.owner.username, tweet.text, "#" + originHashtag)
                sendMessage(c, "wait" + str(len(buffer)), True)
                sendMessage(c, buffer, False)
                state = "standby"
                
            elif state == exitFlag:
                ## do some cleanup and close the connecdtion, exit the thread through the break statement
                print("Received exit signal. Closing connection...")
                c.close()
                loggedUser = None
                try:
                    connectedUsers.pop(loggedUser.username)
                except:
                    pass ## duplicate client connection
                
                break
                state = "standby"

    except (Exception):
        traceback.print_exc()
        
        allowNew = True
        print("Disconnected from client, killing thread..")

thread_lock = threading.Lock() 

## global data common to all connections and threads
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
        ## accept new connections from the main thread
        print("Listening on port " + str(port))
        conn, addr = s.accept()
        connections.append((conn, addr))
        ##newThread = thread_lock.acquire()
        ##threads.append(newThread)
        print("New client connection established from " + str(addr[0]) + " on port " + str(addr[1]))
        
        start_new_thread(threadExecute, (conn,)) ## start a thread and a connection
        if len(connections) >= 5: ## check that connection limit is not exceeded
            print("Connection maximum reached, blocking new requests until a client disconnects.")
            allowNew = False
        