# Sources
# Python Socket Documentation: https://docs.python.org/3/library/socket.html
# Python TCP Guide: https://steelkiwi.com/blog/working-tcp-sockets/

import sys
import socket
import time


## Parameter Handling

args = sys.argv
numArgs = len(sys.argv)
command = 1  ## 0 upload    1 download

if numArgs < 4:
    print("Error: Invalid parameters. Make sure you specify all parameters in the correct format.")
    exit()

params = {}
try:
    params = {"ip": args[2], "port": int(args[3])}
except:
    print("Error: Invalid parameters. Make sure you specify all parameters in the correct format.")


if args[1] == "-u":
    command = 0
    params["message"] = args[4]
elif args[1] == "-d":
    pass
else:
    print("Error: Invalid arguments. Please specify -u for upload and -d for download.")

if command == 0 and len(params["message"]) > 150:
    print("Error: Cannot proceed. Message exceeds 150 characters.") ## not allow empty msg
    exit()




## Open socket for communication


conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    conn.connect((params["ip"], params["port"]))
except:
    print("Error: Could not establish connection with the server at the address and port specified. Make sure the parameters are valid and that the server is running. ")
    exit()


newFlag = b'NEW       '
dowFlag = b'DOW       '  
endFlag = b'END       '

if command == 0:
    size = len(params["message"])
    msg = bytes(params["message"])

    conn.send(newFlag)
    sent = 0
    rem = size
    while sent < size:
        buff = msg[sent:sent+10]
        if len(buff) < 10:
            buff = buff + b' '*(10-len(buff))
        processed = conn.send(buff)
        sent = sent + processed   
    conn.send(endFlag)
    print("Upload succesfull.")
elif command == 1:
    print("Requesting the message")
    conn.send(dowFlag)
    received = conn.recv(150).decode("utf-8")
    print("Output: " + received)
else:
    print("Error: invalid arguments")














