import subprocess, time, os
from PySide.QtGui import *
from PySide import QtCore
from PySide.QtCore import *
from client import Client
from main import Engine
from message import *

class ThreadDispatcher(QThread):
    def __init__(self, parent):
        QThread.__init__(self)
        self.client = Client('192.168.3.105', 8000, "julie", self)
        self.parent = parent
        self.name = ""
        self.running = True
        self.host = ""

    def run(self):
        while self.running:
            if not self.client.outLauncherQueue.empty():
                msg = self.client.outLauncherQueue.get()
                #self.transition(2) or self.name.setText(
                if type(msg) == sendRoom:
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.listPlayers.clear()))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.transition(2)))
                    st =[ p.get('username', 'unknown') +"         status: "+("ready" if p.get('ready', False) else "not ready")+"           Wins: "+str(p.get('wins'))+"           Games: "+str(p.get('games')) for p in msg.playerlist]
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.listPlayers.addItems(st)))
                    QApplication.postEvent(self.parent, _Event(lambda:self.parent.name.setText(str(msg.roomId)) ))
                    self.host = msg.host
                    if self.name == msg.host and self.parent.maps.count()==0:
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.maps.clear()))
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.maps.addItem("Random")))
                        temp = [filename for dirname, dirnames, filenames in os.walk('./saves') for filename in filenames]
                        QApplication.postEvent(self.parent, _Event(lambda: self.parent.maps.addItems(temp)))
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.maps.setCurrentIndex(0)))
                    elif self.name != msg.host:
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.maps.clear()))
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.maps.addItem("Random" if not msg.current_game else msg.current_game)))
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.maps.setCurrentIndex(0)))
                elif type(msg) == startGame:
                    QApplication.postEvent(self.parent, _Event(lambda:Engine(1, self.name, msg.player_turn, msg.seed,self.client, len(msg.player_list), msg.saved_game)))
                    
                elif type(msg) ==LoginAck:
                    if msg.success:
                        QApplication.postEvent(self.parent, _Event(lambda:self.parent.transition(1)))
                    else:
                        print("Could not login")
                elif type(msg) == SendRoomList:
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

    def loadMap(self, mapName):

        if self.host == self.name:
            temp = None
            if mapName != "Random":
                try:
                    with open("./saves/"+mapName, 'rb') as f:
                        temp = f.read()
                except:
                    pass
            self.client.inQueue.put(ChangeMap(mapName, temp))


class _Event(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, callback):
        #thread-safe
        QEvent.__init__(self, _Event.EVENT_TYPE)
        self.callback = callback

class HoverButton(QPushButton):
    def __init__(self, text, parent):
        super().__init__(text,parent)
        self.setStyleSheet("background-color:#333333; font-family : 'Becker'; color: #009933; border-style: outset; border-width: 0px;")
        
    def enterEvent(self,event):
        self.setStyleSheet("background-color:#555555; font-family : 'Becker'; color: #996633; border-style: outset; border-width: 0px;")

    def leaveEvent(self,event):
        self.setStyleSheet("background-color:#333333; font-family : 'Becker'; color: #009933; border-style: outset; border-width: 0px;")

class MoveBar(QPushButton):
    def __init__(self,parent,text='Medieval Warfare'):
        super().__init__(text,parent)
        self.posWin = ()
        self.parent = parent
        self.moveWin = False
        
        self.setStyleSheet("background-color:#009933; color: #000000; font-size : 13px; font-family : 'Livingstone'; border-style: outset; border-width: 0px;")

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

        title = QLabel(self)
        title.setText("Medieval Warfare")
        title.setStyleSheet("font-size : 45px; font-family : 'Prince Valiant'; color : #009933;")
        fields.addWidget(title)
        
        username = QLineEdit(self)
        username.setStyleSheet("background-color:#ffffff; font-family : 'Impact'; color: #009933; border: 0px outset #aaaaaa;")
        username.setText("Username")
        fields.addWidget(username)        

        pw = QLineEdit(self)
        pw.setStyleSheet("background-color:#ffffff; font-family : 'Impact'; color: #009933; border: 0px outset #aaaaaa;")
        pw.setText("Password")
		pw.QLineEdit(Password)
        fields.addWidget(pw)

        spacer1 = QWidget(self)
        spacer1.setFixedSize(100,200)
        fields.addWidget(spacer1)
        
        layout2.addLayout(fields)

        buttons = QVBoxLayout()
        refresh = HoverButton('Login', self)
        refresh.setFixedSize(100,60)
        refresh.clicked.connect(lambda: self.dispatcher.client.inQueue.put(ClientLogin(username.text(), pw.text())) or setattr(self.dispatcher, 'name', username.text()) )
        buttons.addWidget(refresh)
        sign = HoverButton('Sign up', self)
        sign.setFixedSize(100,60)
        sign.clicked.connect(lambda: self.dispatcher.client.inQueue.put(Signup(username.text(), pw.text())) or setattr(self.dispatcher, 'name', username.text()) )
        buttons.addWidget(sign)

        spacer2 = QWidget(self)
        spacer2.setFixedSize(100,10)
        buttons.addWidget(spacer2)

        copyright = QLabel(self)
        copyright.setText("Copyright by Medusa's Coders")
        copyright.setStyleSheet("font-family : Calibri; font-size : 8px; color : #996633")

        layout2.addLayout(buttons)
        knightPic = QPixmap("LauncherKnight.png")
        label = QLabel(self)
        label.setPixmap(knightPic)

        layout2.addWidget(label)
        fields.addWidget(copyright)	
        self.windows['0'] = self.screen0
        return self.screen0
        
    def lobbylist(self):
        self.screen1 =QWidget()
        layout2 = QHBoxLayout()
        self.screen1.setLayout(layout2)
        self.listLobby = QListWidget()
        self.listLobby.setAlternatingRowColors(True)
        self.listLobby.setStyleSheet("background-color:#ffffff; font-family : 'Segoe Script'; color: #000000; border: 0px outset #aaaaaa;")
       
        layout2.addWidget(self.listLobby)

        buttons = QVBoxLayout()
        
        join = HoverButton('Join Room', self)
        join.setFixedSize(100,60)
        #self.transition(2) or self.name.setText(self.listLobby.currentItem().text() if self.listLobby.currentItem() else "")
        join.clicked.connect(lambda: self.dispatcher.client.inQueue.put(JoinRoom(self.listLobby.currentItem().text())) if self.listLobby.currentItem() else False) #subprocess.Popen("python main.py", shell = True)
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
        self.listPlayers.setStyleSheet("background-color:#ffffff; font-family : 'Segoe Script'; color: #000000; border: 0px outset #aaaaaa;")
        layout2.addWidget(self.listPlayers)

        buttons = QVBoxLayout()

        buttons.setSpacing(0)
        buttons.setContentsMargins(0,0,0,0)
        self.name = QLabel("Lobby 1")
        self.name.setStyleSheet("font-size: 20px; font-family : 'Prince Valiant'; color: #009933;")
        self.name.setFixedSize(100,30)
        buttons.addWidget(self.name)
        
        spacer = QWidget(self)
        spacer.setFixedSize(100,40)
        buttons.addWidget(spacer)

        mapName = QLabel("Map:")
        mapName.setStyleSheet("font-size: 14px; font-family : 'Prince Valiant'; color: #009933; ")
        mapName.setFixedSize(100,30)
        buttons.addWidget(mapName)
        
        self.maps = QComboBox(self)
        self.maps.setStyleSheet("background-color:#ffffff; font-family : 'Becker'; color: #009933; border: 0px outset #aaaaaa;font-size: 10px; ")
        self.maps.currentIndexChanged[str].connect(lambda: self.dispatcher.loadMap(self.maps.currentText()))

        buttons.addWidget(self.maps)
        join = HoverButton('Ready', self)
        join.setFixedSize(100,60)
        join.clicked.connect(lambda: self.dispatcher.client.inQueue.put(ReadyForGame())) #subprocess.Popen("python main.py", shell = True)
        #Engine(1, "aaron", 1, 89,self.dispatcher.client)
        buttons.addWidget(join)

        refresh = HoverButton('Back', self)
        refresh.setFixedSize(100,60)
        refresh.clicked.connect(lambda: self.transition(1) or self.dispatcher.client.inQueue.put(LeaveRoom()) or self.maps.clear())
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
