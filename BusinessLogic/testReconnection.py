import pickle
from client import Client
from message import *
import socket


# server
import time

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("localhost", 8001))
s.listen(2)

# client
c = Client("localhost", 8001, "john", None)

# connect
i = s.accept()[0]



# test

# test send
c.inQueue.put("hi")
time.sleep(0.2)
m = i.recv(1024)
assert(pickle.loads(m[3:]) == "hi")

# test receive
msg = ChatMessage("server", "hey")
pmessage = pickle.dumps(msg)
header = "{}{}".format(len(pmessage), "\n").encode()
i.sendall(header + pmessage)
assert(c.outGameQueue.get().message == "hey")

# test reconnect
assert(c.outputThread.is_alive() is True)
c.s.close()
assert(c.outputThread.is_alive() is False) # might fail if reconnect is fast
time.sleep(2)
assert(c.outputThread.is_alive() is True)
ii = s.accept()[0]
assert(ii != i)
i = ii

# test send
c.inQueue.put("hi")
time.sleep(0.2)
m = i.recv(1024)
assert(pickle.loads(m[3:]) == "hi")

# test receive
msg = ChatMessage("server", "hey")
pmessage = pickle.dumps(msg)
header = "{}{}".format(len(pmessage), "\n").encode()
i.sendall(header + pmessage)
assert(c.outGameQueue.get().message == "hey")

# test clear inQueue
c.s.close()
c.inQueue.put("hey")
c.inQueue.put("hey")
c.inQueue.put("hey")
time.sleep(2)
assert(c.inQueue.empty() is True)

print("test passed!")
