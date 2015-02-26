import subprocess, time
from PySide.QtGui import *
from PySide import QtCore
from PySide.QtCore import *
from client import Client
from main import Engine
from message import *

class ThreadDispatcher(QThread):
    def __init__(self, parent):
        QThread.__init__(self)
        self.client = Client('142.157.148.89', 8000, "aaron", self)
        self.parent = parent
        self.running = True

    def run(self):
        while self.running:
            if not self.client.outQueue.empty():
                msg = self.client.outQueue.get()
                #self.transition(2) or self.name.setText(
                if type(msg) == sendRoom:
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.listPlayers.clear()))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.transition(2)))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.listPlayers.addItems(msg.playerlist)))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.name.setText(str(msg.roomId)) ))
                elif type(msg) ==LoginAck:
                    if msg.success:
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.transition(1)))
                    else:
                        print("Could not login")
                elif type(msg) == SendRoomList:
                    print("ids: "+str(msg.room_list))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.listLobby.clear()))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.listLobby.addItems([str(id) for id in msg.room_list])))
                elif msg is None:
                    break
            #QApplication.postEvent(self.parent, _Event(lambda:self.parent.listLobby.addItem("hello")))
            time.sleep(.1)

    def stop(self):
        #idle_loop.put(None)
        #self.wait()
        self.running = False
        self.client.s.close()

class _Event(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, callback):
        #thread-safe
        QEvent.__init__(self, _Event.EVENT_TYPE)
        self.callback = callback

class HoverButton(QPushButton):
    def __init__(self, text, parent):
        super().__init__(text,parent)
        self.setStyleSheet("background-color:#333333; color: #ffffff; border-style: outset; border-width: 0px;")
        
    def enterEvent(self,event):
        self.setStyleSheet("background-color:#555555; color: #ffffff; border-style: outset; border-width: 0px;")

    def leaveEvent(self,event):
        self.setStyleSheet("background-color:#333333; color: #ffffff; border-style: outset; border-width: 0px;")

class MoveBar(QPushButton):
    def __init__(self,parent,text=''):
        super().__init__(text,parent)
        self.posWin = ()
        self.parent = parent
        self.moveWin = False
        
        self.setStyleSheet("background-color:#333333; color: #aaaaaa; border-style: outset; border-width: 0px;")

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        place = event.globalPos()
        if self.moveWin:
            self.parent.move(place.x()-self.posWin.x(),place.y()-self.posWin.y())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.posWin = event.pos()
        self.moveWin = True

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.moveWin = False

class Main(QWidget):
    def __init__(self):
        app = QApplication([])
        super().__init__()
        self.windows = {}
        self.dispatcher = ThreadDispatcher(self)
     
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(600, 300)
        self.move(300, 300)
        self.setWindowTitle('Simple')

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0,0,0,0)
        
        temp = QWidget()
        top = QHBoxLayout()

        top.setContentsMargins(0,0,0,0)
        top.setSpacing(0)

        self.bar = MoveBar(self)
        self.bar.setFixedSize(600+40,20)
        self.bar.setFixedHeight(20)
        self.bar.move(0,0)
        top.addWidget(self.bar)
    
        self.min = HoverButton('    _    ', self)
        self.min.clicked.connect(self.showMinimized)
        self.min.setFixedHeight(20)
        top.addWidget(self.min)
        self.button = HoverButton('    x    ', self)
        self.button.clicked.connect(self.close)
        self.button.setFixedHeight(20)
        top.addWidget(self.button)

        temp.setLayout(top)
        #self.menu.setCornerWidget(temp)
        self.mainLayout.addWidget(temp)
        #self.mainLayout.setMenuBar(self.menu)   
        
        layout1 = QHBoxLayout()
        self.mainLayout.addLayout(layout1)
                   
        self.setStyleSheet("background-color:#333333; color: #ffffff; border: 0px outset #aaaaaa;")
        layout1.addWidget(self.loginScreen())
        layout1.addWidget(self.lobbylist())
        layout1.addWidget(self.lobby())
        self.setLayout(self.mainLayout)
        self.show()
        self.dispatcher.start()
        app.exec_()
        self.dispatcher.stop()

    def customEvent(self, event):
        #process idle_queue_dispatcher events
        event.callback()

    def loginScreen(self):
        self.screen0 =QWidget()
        layout2 = QHBoxLayout()
        self.screen0.setLayout(layout2)

        fields = QVBoxLayout()
        spacer = QWidget(self)
        spacer.setFixedSize(100,100)
        fields.addWidget(spacer)
        
        username = QLineEdit(self)
        username.setStyleSheet("background-color:#ffffff; color: #000000; border: 0px outset #aaaaaa;")
        username.setText("username")
        fields.addWidget(username)        

        pw = QLineEdit(self)
        pw.setStyleSheet("background-color:#ffffff; color: #000000; border: 0px outset #aaaaaa;")
        pw.setText("password")
        fields.addWidget(pw)

        spacer1 = QWidget(self)
        spacer1.setFixedSize(100,200)
        fields.addWidget(spacer1)
        
        layout2.addLayout(fields)

        buttons = QVBoxLayout()
        refresh = HoverButton('Login', self)
        refresh.setFixedSize(100,60)
        refresh.clicked.connect(lambda: self.dispatcher.client.inQueue.put(ClientLogin(username.text())))
        buttons.addWidget(refresh)

        spacer2 = QWidget(self)
        spacer2.setFixedSize(100,10)
        buttons.addWidget(spacer2)

        layout2.addLayout(buttons)
        self.windows['0'] = self.screen0
        return self.screen0
        
    def lobbylist(self):
        self.screen1 =QWidget()
        layout2 = QHBoxLayout()
        self.screen1.setLayout(layout2)
        self.listLobby = QListWidget()
        self.listLobby.setAlternatingRowColors(True)
        self.listLobby.setStyleSheet("background-color:#ffffff; color: #000000; border: 0px outset #aaaaaa;")
       
        layout2.addWidget(self.listLobby)

        buttons = QVBoxLayout()
        
        join = HoverButton('Join Room', self)
        join.setFixedSize(100,60)
        #self.transition(2) or self.name.setText(self.listLobby.currentItem().text() if self.listLobby.currentItem() else "")
        join.clicked.connect(lambda: self.dispatcher.client.inQueue.put(JoinRoom(int(self.listLobby.currentItem().text()))) if self.listLobby.currentItem() else False) #subprocess.Popen("python main.py", shell = True)
        buttons.addWidget(join)

        create = HoverButton('Create Room', self)
        create.setFixedSize(100,60)
        create.clicked.connect(lambda: self.dispatcher.client.inQueue.put(CreateRoom())) #subprocess.Popen("python main.py", shell = True)
        buttons.addWidget(create)

        refresh = HoverButton('Refresh', self)
        refresh.setFixedSize(100,60)
        refresh.clicked.connect(lambda: self.dispatcher.client.inQueue.put(GetRoomList())) #subprocess.Popen("python main.py", shell = True)
        buttons.addWidget(refresh)

        layout2.addLayout(buttons)
        self.windows['1'] = self.screen1
        self.screen1.hide()
        return self.screen1

    def lobby(self):
        self.screen2 =QWidget()
        layout2 = QHBoxLayout()
        self.screen2.setLayout(layout2)
        self.listPlayers = QListWidget()
        self.listPlayers.setAlternatingRowColors(True)
        self.listPlayers.setStyleSheet("background-color:#ffffff; color: #000000; border: 0px outset #aaaaaa;")
        layout2.addWidget(self.listPlayers)

        buttons = QVBoxLayout()

        buttons.setSpacing(0)
        buttons.setContentsMargins(0,0,0,0)
        self.name = QLabel("Lobby 1")
        self.name.setStyleSheet("font-size: 20px; ")
        self.name.setFixedSize(100,30)
        buttons.addWidget(self.name)
        
        spacer = QWidget(self)
        spacer.setFixedSize(100,40)
        buttons.addWidget(spacer)

        mapName = QLabel("Map:")
        mapName.setStyleSheet("font-size: 14px; ")
        mapName.setFixedSize(100,30)
        buttons.addWidget(mapName)
        
        combo = QComboBox(self)
        combo.setStyleSheet("background-color:#ffffff; color: #000000; border: 0px outset #aaaaaa;font-size: 10px; ")
        combo.addItem("Map 1")
        combo.addItem("Map 2")
        combo.addItem("Map 3")
        combo.addItem("Map 4")
        combo.addItem("Map 5")

        buttons.addWidget(combo)
        join = HoverButton('Ready', self)
        join.setFixedSize(100,60)
        join.clicked.connect(lambda: Engine(1, "aaron", 1, 89,self.dispatcher.client)) #subprocess.Popen("python main.py", shell = True)
        buttons.addWidget(join)

        refresh = HoverButton('Back', self)
        refresh.setFixedSize(100,60)
        refresh.clicked.connect(lambda: self.transition(1) or self.dispatcher.client.inQueue.put(LeaveRoom()))
        buttons.addWidget(refresh)

        spacer1 = QWidget(self)
        spacer1.setFixedSize(100,100)
        buttons.addWidget(spacer1)
        
        layout2.addLayout(buttons)
        self.screen2.hide()
        self.windows['2'] = self.screen2
        return self.screen2

    def transition(self, n):
        if n == 0:
            self.windows['0'].show()
            self.windows['2'].hide()
            self.windows['1'].hide()
        if n == 1:
            self.windows['0'].hide()
            self.windows['2'].hide()
            self.windows['1'].show()
        elif n == 2:
            self.windows['0'].hide()
            self.windows['1'].hide()
            self.windows['2'].show()
 
#self.button.setStyleSheet("background-color:" + color.name())

    
main = Main()


#status = subprocess.call("python main.py", shell=True)
