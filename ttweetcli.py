import socket
import sys



args = sys.argv
numArgs = len(args)

if numArgs < 4:
    print("Error: Invalid parameters. Make sure you specify all parameters in the correct format.")
    exit()

params = {}
try:
    params = {"ip": args[1], "port": int(args[2]), "user": args[3]}
except:
    print("Error: Invalid parameters. Make sure you specify all parameters in the correct format.")


if not (params["user"].isalnum()):
    exit()



ipAddr = params["ip"]
port = params["port"]
username = params["user"]

#initialize the socket
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#connect to socket
try:
    soc.connect((ipAddr, port))
except:
    print("Error: Could not establish connection with the server at the address and port specified. Make sure the parameters are valid and that the server is running. ")
    exit()

size = len(username)

sizeString = str(size)

    if (size < 10) :

        sizeString = "00" + sizeString

    elif (size < 100) :

        sizeString = "0" + sizeString

msg = bytes(sizeString + "user" + username)

soc.sendall(msg)

isUser = soc.recv(4).decode("utf-8")

if isUser == 'fail' :

    soc.close()
    exit()

else:

    getCommand()


def getCommand() :

    #get user command
    userArgs = sys.argv
    commandArgs = userArgs.partition(" ")
    checkCommand(commandArgs, userArgs)


#determine what type of command the user recieves
def checkCommand(commandArgs, userArgs) :

    if commandArgs[0] == "tweet" :
        tweet(commandArgs, userArgs)
    elif commandArgs[0] == "subscribe" :
        subscribe(commandArgs, userArgs)
    elif commandArgs[0] == "unsubscribe" :
        unsubscribe(commandArgs, userArgs)
    elif commandArgs[0] == "timeline" :
        timeline(commandArgs, commandArgs)
    elif commandArgs[0] == "exit" :
        exitServer(commandArgs, userArgs)
    else :
        print("Error: Invalid Command")
        #handle invalid command




def tweet(commandArgs, userArgs) :

    #do error handling




    messageType = commandArgs[0]

    #should be of the form [twee"<message>"+++#...]
    message = messageType[0:4] + commandArgs[1] + "+++" + commandArgs[2]

    size = len(message) - 4

    sizeString = str(size)

    if (size < 10) :

        sizeString = "00" + sizeString

    elif (size < 100) :

        sizeString = "0" + sizeString


    #msg should be of the form[000twee"<message>"+++#...]
    msg = bytes(sizeString + message)

    #sends the message to the server
    soc.sendall(msg)
    print("Uploaded Message")

    #loop back to be able to send new message
    print("")
    getCommand()


def subscribe(commandArgs, userArgs) :

    #do error handling

    messageType = commandArgs[0]

    #should be of the form [subs#...]
    message = messageType[0:4] + commandArgs[1]

    size = len(message) - 4

    sizeString = str(size)

    if (size < 10):

        sizeString = "00" + sizeString

    elif (size < 100):

        sizeString = "0" + sizeString

    #should be of the form [000subs#...]
    msg = bytes(sizeString + message)

    # sends the message to the server
    soc.sendall(msg)

    success = soc.recv(4).decode("utf-8")

    if (success == "true"):

        print("Subscribed To Hashtag")

    else :

        print("Failed to Subscribe to Hashtag")

    # loop back to be able to send new message
    getCommand()

def unsubscribe(commandArgs, userArgs) :

    # do error handling

    # get the size and set the message as "size" + message

    messageType = commandArgs[0]

    #should be of the form [unsu#...]
    message = messageType[0:4] + commandArgs[1]

    size = len(message) - 4

    sizeString = str(size)

    if (size < 10):

        sizeString = "00" + sizeString

    elif (size < 100):

        sizeString = "0" + sizeString

    #message should be of the form [000unsu#...]
    msg = bytes(sizeString + message)

    # sends the message to the server
    soc.sendall(msg)

    print("Unsubscribed From Hashtag")

    # loop back to be able to send new message
    getCommand()

def timeline(commandArgs, userArgs) :
    # do error handling

    # get the size and set the message as "size" + message
    messageType = commandArgs[0]

    message = messageType[0:4]

    size = len(message) - 4

    sizeString = str(size)

    if (size < 10):

        sizeString = "00" + sizeString

    elif (size < 100):

        sizeString = "0" + sizeString

    msg = bytes(sizeString + message)

    # sends the message to the server
    soc.sendall(msg)
    print("Requested Timeline")

    #prepare to recieve all of the tweets

    digitString = soc.recv(7).decode("utf-8")

    digits = int(digitString[0:3])

    bytesString = soc.recv(digits).decode("utf-8")

    numBytes = int(bytesString)

    userTimeline = soc.recv(numBytes).decode("utf-8")

    tweets = userTimeline.partition("+++")

    for t in tweets :

        print(t)

    # loop back to be able to send new message
    getCommand()

def exitServer(commandArgs, userArgs) :

    msg = bytes("000exit")

    soc.sendall(msg)

    soc.close()
    exit()

















