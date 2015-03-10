import pygame, sys,math,  numpy as np, OpenGL.arrays.vbo as glvbo, threading, os, sys, pickle,socket, select, string,queue, time, random
from message import *
from client import Client
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.raw import GL as g
from OpenGL.GL import shaders
from OpenGL.GLU import *
from ctypes import util
from OpenGL.arrays import ArrayDatatype as ADT
from tkinter import Tk
from tkinter import filedialog

class Text:
    a = 0.125
    pos = {"0":(0,5),"1":(1,5),"2":(2,5),"3":(3,5),"4":(4,5),"5":(5,5),"6":(6,5),"7":(7,5),
           "8":(0,4),"9":(1,4),
           "a":(1,3),"b":(2,3),"c":(3,3),"d":(4,3),"e":(5,3),"f":(6,3),"g":(7,3),
           "h":(0,2),"i":(1,2),"j":(2,2),"k":(3,2),"l":(4,2),"m":(5,2),"n":(6,2),"o":(7,2),
           "p":(0,1),"q":(1,1),"r":(2,1),"s":(3,1),"t":(4,1),"u":(5,1),"v":(6,1),"w":(7,1),
           "x":(0,0),"y":(1,0),"z":(2,0), "!":(1,7), ":":(2,4), "\"":(2,7),"#":(3,7),"$":(4,7),
           "%":(5,7),"'":(7,7),"(":(0,6),")":(1,6),"*":(2,6),"+":(3,6),",":(4,6),"-":(5,6),
           ".":(6,6),"/":(7,6),";":(3,4),"<":(4,4),"=":(5,4),">":(6,4),"?":(7,4),"[":(3,0),
           "\\":(4,0),"]":(5,0),"^":(6,0),"_":(7,0)}
    image = None
    def __init__(self,i,j,size,text, c=[0,0,0,1]):
        self.offsetbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.offsetbuffer)
        self.texbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.texbuffer)
        self.vertexbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.vertexbuffer)
        self.texoffbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.texoffbuffer)
        self.colorbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.colorbuffer)
        self.size = size
        self.centre = [i,j]
        self.colour = c
        self.changeText(text, i, j)

    def changeText(self,text, i, j):
        x = self.centre[0] = i
        y = self.centre[1] = j
        size = self.size
        
        centres=[]
        verts=[]
        n = 0
        rows = 1
        for c in text:
            if c == ".":
                x =self.centre[0]
                y =self.centre[1]- 2*size*rows
                rows+=1
                n = -1
            elif c == '\n':
                pass
            elif c!=" ":
                centres+=[x+size*n*2,y]
                p = self.pos.get(c,(0,3))
                verts+=[self.a*p[0], self.a*p[1]]
            n+=1

        self.text =text
        self.length = int(len(centres)/2)

        texVerts = np.array([[0,.065],[.045,.065],[.045,.125],[0,.125]], dtype=np.float32)
        off_data = np.array(centres, dtype=np.float32)
        g_tex_buffer_data = np.array([[-size,-size],[size,-size],[size,size],[-size,size]]*len(centres)  , dtype=np.float32)
        texoffVerts = np.array(verts , dtype=np.float32)
        colour_data = np.array(self.colour*4 , dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.offsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(off_data), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(off_data), ADT.voidDataPointer(off_data), GL_STREAM_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.texbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texVerts ), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texVerts ), ADT.voidDataPointer(texVerts ), GL_STREAM_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), ADT.voidDataPointer(g_tex_buffer_data), GL_STREAM_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texoffVerts ), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texoffVerts ), ADT.voidDataPointer(texoffVerts ), GL_STREAM_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.colorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(colour_data), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(colour_data), ADT.voidDataPointer(colour_data), GL_STREAM_DRAW)
        
    def update(self):
        self.draw()

    def draw(self):
        glBindTexture(GL_TEXTURE_2D, self.image)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.colorbuffer)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.offsetbuffer)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(3)
        glBindBuffer(GL_ARRAY_BUFFER, self.texbuffer)
        glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(4)
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, 0, None)

        glVertexAttribDivisor(0, 0)
        glVertexAttribDivisor(1, 0)
        glVertexAttribDivisor(2, 1)
        glVertexAttribDivisor(3, 0)
        glVertexAttribDivisor(4, 1)
        glVertexAttribDivisor(5, 1)

        #glDrawArrays(GL_QUADS, 0, 4*self.length)
        glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 4, self.length)

        glVertexAttribDivisor(0, 0)
        glVertexAttribDivisor(1, 0)
        glVertexAttribDivisor(2, 0)
        glVertexAttribDivisor(3, 0)
        glVertexAttribDivisor(4, 0)
        glVertexAttribDivisor(5, 0)

        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(2)
        glDisableVertexAttribArray(3)
        glDisableVertexAttribArray(4)

class Element:
    def __init__(self, x, y, w, h,c):
        self.centre = [x, y]
        self.h = h
        self.w = w

        self.texVerts = np.array([0,0,0,0]*4 , dtype=np.float32)
        self.texbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.texbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, self.texbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texVerts ), ADT.voidDataPointer(self.texVerts ), GL_STATIC_DRAW)
        
        g_tex_buffer_data = np.array([[-w+x,-h+y],[w+x,-h+y],[w+x,h+y],[-w+x,h+y]] , dtype=np.float32)
        self.vertexbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.vertexbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), ADT.voidDataPointer(g_tex_buffer_data), GL_STATIC_DRAW)

        self.texoffVerts = np.array(c*4 , dtype=np.float32)
        self.texoffbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.texoffbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texoffVerts ), ADT.voidDataPointer(self.texoffVerts ), GL_STATIC_DRAW)

    def inSquare(self, p, t):
        return (self.centre[0]+t+self.w>p[0]>self.centre[0]+t-self.w and self.centre[1]+self.h>p[1]>self.centre[1]-self.h)

    def changeColour(self,c):
        self.texoffVerts = np.array(c*4 , dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texoffVerts ), None, GL_DYNAMIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texoffVerts ), ADT.voidDataPointer(self.texoffVerts ), GL_DYNAMIC_DRAW)

    def update(self):
        g_tex_buffer_data = np.array([[-self.w+self.centre[0],-self.h+self.centre[1]],[self.w+self.centre[0],-self.h+self.centre[1]],[self.w+self.centre[0],self.h+self.centre[1]],[-self.w+self.centre[0],self.h+self.centre[1]]] , dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), ADT.voidDataPointer(g_tex_buffer_data), GL_STATIC_DRAW)

    def draw(self):
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glVertexAttribPointer(0, 2, GL_FLOAT, False, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.texbuffer)
        glVertexAttribPointer(1, 4, GL_FLOAT, False, 0, None)
        glEnableVertexAttribArray(5)
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glVertexAttribPointer(5, 4, GL_FLOAT, False, 0, None)

        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(5)

class Button(Element):
    def __init__(self, x, y, w, h, f,fdraw, text, size = 0.015):
        self.colour = [0,0,0,1]
        self.hoverColour = [.5,.5,.5,1]
        self.size = size
        super().__init__(x,y,len(text)*size+0.01,h,self.colour)
        self.clickFunction = f
        self.fdraw = fdraw
       # self.image = bindTexture(image)
        self.text = Text(x-len(text)*(0.9*size),y+size/3,size,text, [1,1,1,1])

    def mouseOver(self,p,t):
        if self.fdraw() and self.inSquare(p,t):
            self.changeColour(self.hoverColour)
        elif self.fdraw():
            self.changeColour(self.colour)

    def update(self, text):
        delta =len(text)*self.size+.01-self.w
        self.w = len(text)*self.size+.01
        self.centre[0] += delta
        self.text.changeText(text, self.centre[0]-self.w+self.size+0.01,self.centre[1]+self.h-self.size-0.01)
        super().update()

    def click(self, p, t):
        if self.fdraw() and self.inSquare(p,t):
            self.clickFunction()
            return True
        return False

    def draw(self):
        if self.fdraw():
            super().draw()
            self.text.draw()
            return True
        return False

class Overlay(Element):
    def __init__(self, x, y, w, h, text, size = 0.03, c = [.5,.5,.5,.9]):
        self.size = size
        w= len(text)*size+.01
        super().__init__(x,y,w,h,c)
        self.text = Text(x-w+size+0.01,y+h-size-0.01,size,text, [1,1,1,1])

    def update(self, text):
        self.w = len(text)*self.size+.01
        self.text.changeText(text, self.centre[0]-self.w+self.size+0.01,self.centre[1]+self.h-self.size-0.01)
        super().update()

    def draw(self):
        super().draw()
        self.text.draw()

class TextField(Element):
    def __init__(self, x, y, w, h,size = 0.02, c = [.8,.8,.8,.9]):
        text = ""
        self.size = size
        super().__init__(x,y,w,h,c)
        self.maxLength = int(self.w/(self.size))
        self.text = Text(x-w+size+0.01,y+h-size-0.01,size,text, [0,0,0,1])

    def update(self, text):
        if len(text)>self.maxLength:
            text = text[-self.maxLength:]
        self.text.changeText(text, self.centre[0]-self.w+self.size,self.centre[1]+self.h-self.size-0.01)

    def draw(self):
        super().draw()
        self.text.draw()

class Path:
    def __init__(self, d):
        self.overlaybuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlaybuffer)

        self.overlaycolorbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlaycolorbuffer)

        self.overlaycffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlaycffsetbuffer)

        self.overlayoffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlayoffsetbuffer)
        
        d-=.05
        g_overlay_buffer_data = np.array([[-d/2,-d*math.sin(math.pi/3)], 
                [d/2,-d*math.sin(math.pi/3)],
                [d,0],
                [d/2,d*math.sin(math.pi/3)], 
                [-d/2,d*math.sin(math.pi/3)], 
                [-d,0]], dtype=np.float32)
        g_overlayColor_buffer_data = np.array([0,0,0,.6]*6, dtype=np.float32)
        

        glBindBuffer(GL_ARRAY_BUFFER, self.overlaybuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlay_buffer_data), ADT.voidDataPointer(g_overlay_buffer_data), GL_STATIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycolorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayColor_buffer_data), ADT.voidDataPointer(g_overlayColor_buffer_data), GL_STATIC_DRAW)
        self.count = 0
       
    def path(self, path):
        self.count = len(path)
        if path:
            g_overlayCOffset_buffer_data = np.array([[1,1,0,0] for h in path], dtype=np.float32)
            g_overlayOffset_buffer_data = np.array([h.centre for h in path], dtype=np.float32)

            glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
            glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), None, GL_STREAM_DRAW)
            glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), ADT.voidDataPointer(g_overlayCOffset_buffer_data), GL_STREAM_DRAW)

            glBindBuffer(GL_ARRAY_BUFFER, self.overlayoffsetbuffer)
            glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayOffset_buffer_data), None, GL_STREAM_DRAW)
            glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayOffset_buffer_data), ADT.voidDataPointer(g_overlayOffset_buffer_data), GL_STREAM_DRAW)

    def draw(self):
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaybuffer)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycolorbuffer)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlayoffsetbuffer)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(5)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 0, None)

        glVertexAttribDivisor(0, 0)
        glVertexAttribDivisor(1, 0)
        glVertexAttribDivisor(2, 1)
        glVertexAttribDivisor(5, 1)

        glDrawArraysInstanced(GL_LINE_LOOP, 0, 6,self.count)

        glVertexAttribDivisor(0, 0)
        glVertexAttribDivisor(1, 0)
        glVertexAttribDivisor(2, 0)
        glVertexAttribDivisor(5, 0)

        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(2)
        glDisableVertexAttribArray(5)

class Chat:
    def __init__(self, aspect, button):
        self.lines = []
        self.width = .8
        self.height = .4
        self.button = button
        self.y = 1-.06-self.height
        self.x = -aspect+self.width
        self.back = Element(-aspect+self.width,self.y,self.width,self.height,[.5,.5,.5,.9])
        self.size = 0.015
        self.text = Text(1,.6,self.size,'')
        self.maxLength = int(self.width/(self.size))
        self.maxLines = int(self.height/(self.size))
        self.newMessages = 0

    def update(self, new, showing):
        if not showing:
            self.newMessages +=1
            self.button.update("chat ("+str(self.newMessages)+")")
        else:
            self.button.update("chat")
        for i in range(0, len(new), self.maxLength):
            self.lines.append(new[i:i+self.maxLength])
        while len(self.lines)>self.maxLines:
            self.lines.pop(0)
        st = '.'.join(self.lines)
        self.text.changeText(st, self.back.centre[0]-self.back.w+self.size,self.back.centre[1]+self.back.h-self.size)

    def draw(self):
        self.back.draw()
        self.text.draw()

class UI:
    def __init__(self, gui):
        self.gui = gui
        self.shift = -self.gui.width/self.gui.height+.1
        self.visible = 0
        self.showMenu = False
        
        self.unitButtons = []
        self.chatButton = Button(-self.gui.width/self.gui.height+4*0.015+0.01,1-.03,.2,.03, lambda: setattr(self.gui, 'showChat', not self.gui.showChat) or self.chatButton.update("chat"), lambda: True, "chat", 0.015)
        self.chat = Chat(self.gui.width/self.gui.height, self.chatButton)
        self.textField = TextField(self.chat.x, self.chat.y-self.chat.height-0.03, self.chat.width,0.03)
        self.chatString = ""

        self.height = -(1-0.03)

        aspect = self.gui.width/self.gui.height

        self.bottomBar = Element(-aspect, self.height,2*aspect, 0.03,[0,0,0,1])
        self.topBar = Element(-aspect, -self.height,2*aspect, 0.03,[0,0,0,1])
        
        self.unitButtons.append(Button(0,self.height,.22,.03, lambda: self.gui.buildMeadow(),lambda: True if self.gui.selected and self.gui.selected.occupant and self.gui.selected.occupant.type<3 and not self.gui.selected.hasMeadow and not self.gui.selected.occupant.moved else False, "build meadow"))
        self.unitButtons.append(Button(0,self.height,.22,.03, lambda: self.gui.buildRoad(),lambda: True if self.gui.selected and self.gui.selected.occupant and self.gui.selected.occupant.type<3 and not self.gui.selected.hasRoad and not self.gui.selected.occupant.moved else False, "build road"))
        self.unitButtons.append(Button(0,self.height,.22,.03, lambda: self.gui.upgradeUnit(1),lambda: True if self.gui.selected and self.gui.selected.occupant and self.gui.selected.occupant.type<1 and self.gui.selected.village.gold>=10*(1-self.gui.selected.occupant.type) else False, "upgrade infantry"))
        self.unitButtons.append(Button(0,self.height,.22,.03, lambda: self.gui.upgradeUnit(2),lambda: True if self.gui.selected and self.gui.selected.occupant and self.gui.selected.occupant.type<2 and self.gui.selected.village.type and self.gui.selected.village.gold>=10*(2-self.gui.selected.occupant.type) >0 else False, "upgrade soldier"))
        self.unitButtons.append(Button(0,self.height,.22,.03, lambda: self.gui.upgradeUnit(3), lambda: True if self.gui.selected and self.gui.selected.occupant and self.gui.selected.occupant.type<3 and self.gui.selected.village.type >1 and not self.gui.selected.occupant.action and self.gui.selected.village.gold>=10*(3-self.gui.selected.occupant.type) else False, "upgrade knight"))
        self.unitButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.buildWatchTower(),lambda: True if self.gui.selected and self.gui.selected.village.wood>=5 and self.gui.selected.village.type >0 and not self.gui.selected.hasWatchTower else False, "build tower"))
        self.villageButtons = []
        self.hexButtons = []
        
        self.hexButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.spawnUnit(0),lambda: True if self.gui.selected and self.gui.selected.village and self.gui.selected.village.gold>=10  else False, "buy peasant"))
        self.hexButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.spawnUnit(1),lambda: True if self.gui.selected and self.gui.selected.village and self.gui.selected.village.gold>=20 else False, "buy infantry"))
        
        self.hexButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.spawnUnit(2),lambda: True if self.gui.selected and self.gui.selected.village and self.gui.selected.village.gold>=30 and self.gui.selected.village.type >0 else False, "buy soldier"))
        self.hexButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.spawnUnit(3),lambda: True if self.gui.selected and self.gui.selected.village and self.gui.selected.village.gold>=40 and self.gui.selected.village.type >1 and  not self.gui.selected.hasTree else False, "buy knight"))
        self.villageButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.upgradeVillage(),lambda: True if self.gui.selected and self.gui.selected.village and self.gui.selected.village.wood>=8 and self.gui.selected.village.type<2 else False, "upgrade town"))
        self.hexButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.buildWatchTower(),lambda: True if self.gui.selected and self.gui.selected.village and self.gui.selected.village.wood>=5 and self.gui.selected.village.type >0 and not self.gui.selected.hasWatchTower else False, "build tower"))
         
        self.combineButtons = []  
        self.combineButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.combine(),lambda: True if self.gui.selected and self.gui.combiner and self.gui.selected.occupant and self.gui.combiner.occupant and  self.gui.selected.village.canCombinetoInfantry(self.gui.selected.occupant, self.gui.combiner.occupant) else False , "combine to infantry"))
        self.combineButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.combine(),lambda: True if self.gui.selected and self.gui.combiner and self.gui.selected.occupant and self.gui.combiner.occupant and self.gui.selected.village.canCombinetoSoldier(self.gui.selected.occupant, self.gui.combiner.occupant) else False , "combine to soldier"))     
        self.combineButtons.append(Button(0,self.height,.2,.03, lambda: self.gui.combine(),lambda: True if self.gui.selected and self.gui.combiner and self.gui.selected.occupant and self.gui.combiner.occupant and self.gui.selected.village.canCombinetoKnight(self.gui.selected.occupant, self.gui.combiner.occupant)  else False, "combine to knight"))
        #self.villageButtons.append(Button(-1.1,self.height,.18,.03, lambda: setattr(self.gui, 'show', not self.gui.show), "territories"))
        self.menuButtons = []
        self.menuButtons.append(Button(0,0.2,.2,.03, lambda: self.gui.save(),lambda: True , "save game"))
        self.menuButtons.append(Button(0,0,.2,.03, lambda: self.gui.load(),lambda: True , "load game"))
        self.menuButtons.append(Button(0,-.2,.2,.03, lambda: pygame.quit() or setattr(self.gui, 'running', False),lambda: True , "exit game"))

        self.endButton = Button(1.5,self.height,.2,.03, lambda: self.gui.endTurn(), lambda: True, "end turn", 0.015)
        

    def mouseOver(self,p):
        t = self.shift
        if self.visible ==1:
            for b in self.hexButtons:
                if b.mouseOver(p,t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1
        elif self.visible ==2:
            for b in self.unitButtons:
                if b.mouseOver(p, t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1
        elif self.visible ==3:
            for b in self.villageButtons:
                if b.mouseOver(p,t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1
        elif self.visible == 4:
            for b in self.combineButtons:
                if b.mouseOver(p,t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1

        if self.showMenu:
            for b in self.menuButtons:
                if b.mouseOver(p,0):
                    return True

        if self.chatButton.mouseOver(p,0):
            return True
        if self.gui.engine.turn == self.gui.player:
            if self.endButton.mouseOver(p,0):
                return True
        return False

    def click(self, p):
        t = self.shift
        if self.visible ==1:
            for b in self.hexButtons:
                if b.click(p,t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1
        elif self.visible ==2:
            for b in self.unitButtons:
                if b.click(p, t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1
        elif self.visible ==3:
            for b in self.villageButtons:
                if b.click(p,t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1
        elif self.visible == 4:
            for b in self.combineButtons:
                if b.click(p,t+b.w):
                    return True
                if b.fdraw():
                    t+=2*b.w+.1

        if self.showMenu:
            for b in self.menuButtons:
                if b.click(p,0):
                    return True

        if self.chatButton.click(p,0):
            return True
        if self.gui.engine.turn == self.gui.player:
            if self.endButton.click(p,0):
                return True
        return False

    def drawHexUI(self):
        self.visible = 1
        t=self.shift
        for b in self.hexButtons:
            glUniform2f(self.gui.transloc,t+b.w,0)
            if b.draw():
                t+= 2*b.w+.1

    def drawUnitUI(self):
        self.visible = 2
        t=self.shift
        for b in self.unitButtons:
            glUniform2f(self.gui.transloc,t+b.w,0)
            if b.draw():
                t+= 2*b.w+.1

    def drawVillageUI(self):
        self.visible = 3
        t=self.shift
        for b in self.villageButtons:
            glUniform2f(self.gui.transloc,t+b.w,0)
            if b.draw():
                t+= 2*b.w+.1

    def drawCombine(self):
        self.visible = 4
        t=self.shift
        for b in self.combineButtons:
            glUniform2f(self.gui.transloc,t+b.w,0)
            if b.draw():
                t+= 2*b.w+.1

    def drawMenu(self):
        for b in self.menuButtons:
            b.draw()

    def drawNone(self):
        self.visible = 0

class Gui:
    def __init__(self, engine, width, height, name, player, client):
        sys.setrecursionlimit(10000)
        self.height = height
        self.width = width
        self.engine = engine
        self.name = name
        self.player = player
        self.mouseDown = False
        pygame.init()
        self.init()
        self.zoom = 1
        self.trans = [0,0]
        self.shader = self.shaders()
        self.selected = None
        self.combiner = None
        self.spriteSheetCuts = (4,5)
        self.altDown = False
        self.shiftDown = False

        self.mainClock = pygame.time.Clock()
        shaders.glUseProgram(self.shader)
        self.transloc= glGetUniformLocation(self.shader,'engine')
        glUniform2f(self.transloc,0,0)
        self.zoomloc = glGetUniformLocation(self.shader,'zoom')
        glUniform1f(self.zoomloc,1)
        self.running = True
        self.client = client

        self.mapTex = self.bindTexture("texture.png")
        self.path = Path(self.engine.grid.d)

        Text.image = self.bindTexture("ExportedFont_Alpha.png")

        self.villageOverlays = {v : Overlay(v.hex.centre[0], v.hex.centre[1]+.05, 0.2, 0.025, "w:"+str(v.wood)+"  g:"+str(v.gold), 0.015, [0.8,0.8,0.8,0.5]) for v in self.engine.players[self.player].villages}

        self.showChat = False
        self.ui = UI(self)
        temp = [0,0,0,0]
        for h in self.engine.grid.hexes.values():
            if h.owner != 0:
                temp[h.owner-1]+=1
        self.text = Overlay(1,.6,0.35,0.2,"territories.player 1:"+str(temp[0])+".player 2:"+str(temp[1])+".player 3:"+str(temp[2])+".player 4:"+str(temp[3]))
        
        #grid
        self.initGridBuffers()

        #objects
        self.initObjectBuffers()

    def init(self):
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50,50)
        pygame.display.set_caption('Medival Warfare','Medival Warfare')
        pygame.display.set_mode((self.width, self.height), OPENGL|DOUBLEBUF)# |FULLSCREEN|HWSURFACE)
        glClearColor(0,0,0,0)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def shaders(self):
        VERTEX_SHADER = shaders.compileShader('''
        #version 330

        layout (location = 0) in vec2 position;
        layout (location = 1) in vec4 color;
        layout (location = 2) in vec2 offset;
        layout (location = 3) in vec2 vertexUV;
        layout (location = 4) in vec2 UVOffset;
        layout (location = 5) in vec4 colorOffsetin;

        uniform vec2 engine;
        uniform float zoom;

        out vec4 theColor;
        out vec4 colorOffset;
        out vec2 UV;
        
        void main()
        {
            vec2 vert = zoom*vec2(((position.x+offset.x+engine.x)/'''+str(self.width/self.height)+'''), (position.y+offset.y+engine.y));
            gl_Position = vec4(vert,0,1);
            UV = vertexUV+UVOffset;
            theColor = color;
            colorOffset = colorOffsetin;
        }
        ''', GL_VERTEX_SHADER)

        FRAGMENT_SHADER = shaders.compileShader("""
        #version 330
        
        in vec4 theColor;
        in vec4 colorOffset;
        in vec2 UV;

        out vec4 outputColor;

        uniform sampler2D myTextureSampler;

        void main()
        {
            if(theColor.a==1){
                outputColor = theColor*texture(myTextureSampler, UV).rgba;
            }
            else{
                outputColor = theColor+colorOffset;                
            }
        }
        """, GL_FRAGMENT_SHADER)

        return shaders.compileProgram(VERTEX_SHADER,FRAGMENT_SHADER)

    def initGridBuffers(self):
        self.gridvertexbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.gridvertexbuffer)

        self.gridcolorbuffer= g._types.GLuint(0);
        glGenBuffers(1, self.gridcolorbuffer)

        self.gridoffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.gridoffsetbuffer)

        self.gridtexbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.gridtexbuffer)

        self.gridUVoffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.gridUVoffsetbuffer)
        
        self.overlaybuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlaybuffer)

        self.overlaycolorbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlaycolorbuffer)

        self.overlaycffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlaycffsetbuffer)

        self.overlayoffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.overlayoffsetbuffer)

        d = self.engine.grid.d
        point_data = np.array([[-d/2,-d*math.sin(math.pi/3)], 
                [d/2,-d*math.sin(math.pi/3)],
                [d,0],
                [d/2,d*math.sin(math.pi/3)], 
                [-d/2,d*math.sin(math.pi/3)], 
                [-d,0]],dtype=np.float32)
        colour_data = np.array([1,1,1,1]*6, dtype=np.float32)
        g_offset_buffer_data = np.array([ h.centre for h in self.engine.grid.hexes.values()], dtype=np.float32)
        texData = [[1/self.spriteSheetCuts[0]*(h[0]+.5),1/self.spriteSheetCuts[1]*(h[1]+.5)] for h in [[-.25,-.5*math.sin(math.pi/3)], 
                                            [.25,-.5*math.sin(math.pi/3)],
                                            [.5,0],
                                            [.25,.5*math.sin(math.pi/3)], 
                                            [-.25,.5*math.sin(math.pi/3)], 
                                            [-.5,0]
                                            ]]
        vert_data = np.array(texData, dtype=np.float32)
        self.gridUVoffsets = [ self.getHexUV(h) for h in self.engine.grid.hexes.values()]
        g_UVoffset_buffer_data = np.array(self.gridUVoffsets, dtype=np.float32)
        d-=.02
        g_overlay_buffer_data = np.array([[-d/2,-d*math.sin(math.pi/3)], 
                [d/2,-d*math.sin(math.pi/3)],
                [d,0],
                [d/2,d*math.sin(math.pi/3)], 
                [-d/2,d*math.sin(math.pi/3)], 
                [-d,0]], dtype=np.float32)
        g_overlayColor_buffer_data = np.array([0,0,0,.6]*6, dtype=np.float32)
        self.overlaycolors = [[0.6118, .0118, 0.2824, 0] if h.owner==1 else ([0.0314, 0.5882, 0.651, 0] if h.owner ==2 else ([0, 0.0196, 0.302,0] if h.owner == 3 else ([.8098,0.3784, 0.0196,0] if h.owner == 4 else [0,0,0,-.6])))  for h in self.engine.grid.land]
        g_overlayCOffset_buffer_data = np.array(self.overlaycolors, dtype=np.float32)
        g_overlayOffset_buffer_data = np.array([h.centre for h in self.engine.grid.land], dtype=np.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.gridvertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(point_data), ADT.voidDataPointer(point_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.gridcolorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(colour_data), ADT.voidDataPointer(colour_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.gridoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_offset_buffer_data), ADT.voidDataPointer(g_offset_buffer_data), GL_STATIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.gridtexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(vert_data), ADT.voidDataPointer(vert_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.gridUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_UVoffset_buffer_data), ADT.voidDataPointer(g_UVoffset_buffer_data), GL_STATIC_DRAW)
       
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaybuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlay_buffer_data), ADT.voidDataPointer(g_overlay_buffer_data), GL_STATIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycolorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayColor_buffer_data), ADT.voidDataPointer(g_overlayColor_buffer_data), GL_STATIC_DRAW)
       
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), ADT.voidDataPointer(g_overlayCOffset_buffer_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.overlayoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayOffset_buffer_data), ADT.voidDataPointer(g_overlayOffset_buffer_data), GL_STATIC_DRAW)

    def initObjectBuffers(self):
        #gen buffers
        self.unitvertexbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.unitvertexbuffer)

        self.unitcolorbuffer= g._types.GLuint(0);
        glGenBuffers(1, self.unitcolorbuffer)

        self.unitoffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.unitoffsetbuffer)

        self.unittexbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.unittexbuffer)

        self.unitUVoffsetbuffer = g._types.GLuint(0);
        glGenBuffers(1, self.unitUVoffsetbuffer)

        self.unitcoloroffbuffer= g._types.GLuint(0);
        glGenBuffers(1, self.unitcoloroffbuffer)

        #gather data
        offset_array = [village.hex.centre for player in self.engine.players.values() for village in player.villages]+[unit.hex.centre for player in self.engine.players.values() for village in player.villages for unit in  village.units]
        self.nObjects = len(offset_array)
        offset_data =  np.array(offset_array, dtype=np.float32)
        texOff_data = np.array([[0,0] for player in self.engine.players.values() for village in player.villages]+[[unit.type/self.spriteSheetCuts[0],3/self.spriteSheetCuts[1]] for player in self.engine.players.values() for village in player.villages for unit in  village.units], dtype=np.float32)
        colour_data = np.array([1,1,1,1]*4, dtype=np.float32)
        size = 0.05
        vertex_data = np.array([[-size,-size],[size,-size],[size,size],[-size,size]], dtype=np.float32)
        texture_data = np.array([[.8*(1/self.spriteSheetCuts[0])*(h[0]+.1),.8*(1/self.spriteSheetCuts[1])*(h[1]+.1)] for h in [[0,0],[1,0],[1,1],[0,1]]], dtype=np.float32)
        color_off_data = np.array([[0,0,0,0]*4], dtype=np.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitvertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(vertex_data), ADT.voidDataPointer(vertex_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitcolorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(colour_data), ADT.voidDataPointer(colour_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(offset_data), ADT.voidDataPointer(offset_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unittexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texture_data), ADT.voidDataPointer(texture_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texOff_data), ADT.voidDataPointer(texOff_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitcoloroffbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(color_off_data), ADT.voidDataPointer(color_off_data), GL_STATIC_DRAW)

    def loadGridBuffers(self):
        g_overlayOffset_buffer_data = np.array([h.centre for h in self.engine.grid.land], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlayoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayOffset_buffer_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayOffset_buffer_data), ADT.voidDataPointer(g_overlayOffset_buffer_data), GL_STATIC_DRAW)

    def getHexUV(self, h):
        ret = [0,0]
        if h.hasWatchTower and h.hasMeadow:
            ret = [3,2]
        elif h.hasWatchTower:
            ret = [2,2]
        elif h.hasRoad and h.hasMeadow:
            ret = [1,2]
        elif h.hasRoad:
            ret = [0,2]
        elif h.hasTombstone and h.hasMeadow:
            ret = [3,1]
        elif h.hasTombstone:
            ret = [2,1]
        elif h.hasTree:
            ret = [1,3]
        elif h.water:
            ret = [3,3]
        elif h.hasMeadow:
            ret = [2,3]
        else:
            ret = [0,3]

        ret[0] /= self.spriteSheetCuts[0]
        ret[1] /= self.spriteSheetCuts[1]
        return ret

    def updateGridBuffers(self):
        #needs change
        #n = self.engine.grid.hexes.index(self.selected)
        #self.gridUVoffsets[n] = [1/self.spriteSheetCuts[0],0] if self.selected.hasTree else ([0,1/self.spriteSheetCuts[1]] if self.selected.water else ([2/self.spriteSheetCuts[0],0] if self.selected.hasMeadow else[0,0]))
        self.gridUVoffsets = [ self.getHexUV(h) for h in self.engine.grid.hexes.values()]
        self.overlaycolors = [[1,0,0,0] if self.selected == h or self.combiner ==h
                              else ([0.6118, .0118, 0.2824, 0] if h.owner==1 
                                   else ([0.0314, 0.5882, 0.651, 0] if h.owner ==2 
                                         else ([0, 0.0196, 0.302,0] if h.owner == 3 
                                               else ([.8098,0.3784, 0.0196,0] if h.owner == 4 
                                                     else [0,0,0,-.6]))))  for h in self.engine.grid.land]

        g_UVoffset_buffer_data = np.array(self.gridUVoffsets, dtype=np.float32)
        g_overlayCOffset_buffer_data = np.array(self.overlaycolors, dtype=np.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.gridUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_UVoffset_buffer_data), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_UVoffset_buffer_data), ADT.voidDataPointer(g_UVoffset_buffer_data), GL_STREAM_DRAW)
            
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), ADT.voidDataPointer(g_overlayCOffset_buffer_data), GL_STREAM_DRAW)
        
    def updateObjectBuffers(self):
        if self.selected and self.selected.village and self.selected.village.owner == self.engine.players[self.player]:
            self.villageOverlays[self.selected.village].update("w:"+str(self.selected.village.wood)+"  g:"+str(self.selected.village.gold))
        for v in self.engine.players[self.player].villages:
            if v not in self.villageOverlays:
                self.villageOverlays[v] = Overlay(v.hex.centre[0], v.hex.centre[1]+.05, 0.2, 0.025, "w:"+str(v.wood)+"  g:"+str(v.gold), 0.015, [0.8,0.8,0.8,0.5])

        temp = []
        for v in self.villageOverlays.keys():
            if v not in self.engine.players[self.player].villages:
                temp.append(v)
        for v in temp:
            del self.villageOverlays[v]     
        offset_array = [village.hex.centre for player in self.engine.players.values() for village in player.villages]+[unit.hex.centre for player in self.engine.players.values() for village in player.villages for unit in  village.units]
        self.nObjects = len(offset_array)
        offset_data =  np.array(offset_array, dtype=np.float32)
        texOff_data = np.array([[village.type/self.spriteSheetCuts[0],0] for player in self.engine.players.values() for village in player.villages]+
                               [[unit.type/self.spriteSheetCuts[0],4/self.spriteSheetCuts[1]] for player in self.engine.players.values() for village in player.villages for unit in  village.units]
                               , dtype=np.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texOff_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texOff_data), ADT.voidDataPointer(texOff_data), GL_STREAM_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(offset_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(offset_data), ADT.voidDataPointer(offset_data), GL_STREAM_DRAW)

    def drawMap(self):
        glBindTexture(GL_TEXTURE_2D, self.mapTex)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridvertexbuffer)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridcolorbuffer)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridoffsetbuffer)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(3)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridtexbuffer)
        glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(4)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridUVoffsetbuffer)
        glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, 0, None)

        glVertexAttribDivisor(0, 0)
        glVertexAttribDivisor(1, 0)
        glVertexAttribDivisor(2, 1)
        glVertexAttribDivisor(3, 0)
        glVertexAttribDivisor(4, 1)
        glVertexAttribDivisor(5, 1)

        glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 6, len(self.engine.grid.hexes))

        glBindBuffer(GL_ARRAY_BUFFER, self.overlaybuffer)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycolorbuffer)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlayoffsetbuffer)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(5)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 0, None)

        glDrawArraysInstanced(GL_LINE_LOOP, 0, 6,len(self.engine.grid.land))

        glBindBuffer(GL_ARRAY_BUFFER, self.unitvertexbuffer)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.unitcolorbuffer)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.unitoffsetbuffer)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.unittexbuffer)
        glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.unitUVoffsetbuffer)
        glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.unitcoloroffbuffer)
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 0, None)

        glVertexAttribDivisor(5, 0)

        glDrawArraysInstanced(GL_TRIANGLE_FAN, 0, 4, self.nObjects)

        glVertexAttribDivisor(0, 0)
        glVertexAttribDivisor(1, 0)
        glVertexAttribDivisor(2, 0)
        glVertexAttribDivisor(3, 0)
        glVertexAttribDivisor(4, 0)
        glVertexAttribDivisor(5, 0)

        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(2)
        glDisableVertexAttribArray(3)
        glDisableVertexAttribArray(4)
        glDisableVertexAttribArray(5)

    def buildMeadow(self):
        self.client.inQueue.put(TurnData('applyBuildMeadow', [self.selected.number]))
        self.selected.occupant.setBuildingMeadow()

    def buildRoad(self):
        self.client.inQueue.put(TurnData('applyBuildRoad', [self.selected.number]))
        self.selected.occupant.setBuildingRoad()

    def upgradeUnit(self, n):
        self.client.inQueue.put(TurnData('applyUpgradeUnit', [self.selected.number, n]))
        self.selected.occupant.upgrade(n)

    def buildWatchTower(self):
        self.client.inQueue.put(TurnData('applyBuildWatchtower', [self.selected.number]))
        self.selected.buildWatchTower()

    def spawnUnit(self, n):
        self.client.inQueue.put(TurnData('applySpawnUnit', [self.selected.number, n]))
        self.selected.village.spawnUnit(self.selected,n)

    def upgradeVillage(self):
        self.client.inQueue.put(TurnData('applyUpgradeVillage', [self.selected.number]))
        self.selected.village.upgrade()

    def combine(self):
        self.client.inQueue.put(TurnData('applyCombine', [self.selected.number, self.combiner.number]))
        self.selected.village.combine(self.selected.occupant, self.combiner.occupant)

    def beginTurn(self):
        if self.engine.rounds and self.engine.turn == 1:
            self.client.inQueue.put(TurnData('growthPhase', []))
            self.engine.growthPhase()
        self.client.inQueue.put(TurnData('beginTurn', [self.player]))
        self.engine.beginTurn(self.player)
        self.updateGridBuffers()
        self.updateObjectBuffers()

    def endTurn(self):
        self.selected = None
        self.combiner = None
        self.ui.visible = 0
        self.client.inQueue.put(TurnData('applyEndTurn', []))
        self.engine.turn = self.engine.turn%len(self.engine.players)+1
        if self.engine.turn == 1:
            self.engine.rounds +=1
        if self.engine.turn == self.player:
            self.beginTurn()

    def applyEndTurn(self):
        self.engine.turn = self.engine.turn%len(self.engine.players)+1
        if self.engine.turn == 1:
            self.engine.rounds +=1
        if self.engine.turn == self.player:
            self.beginTurn()

    def run(self):
        if self.engine.turn == self.player:
           self.beginTurn()
        while self.running:
            clickEvent = False
            if not self.client.outGameQueue.empty():
                temp = self.client.outGameQueue.get()
                clickEvent = True
                if type(temp) == ChatMessage:
                    self.ui.chat.update(temp.message, self.showChat)
                elif type(temp) == TurnData:
                    if temp.fname == 'applyEndTurn':
                        self.applyEndTurn()
                    else:
                        try:
                            getattr(self.engine,temp.fname)(*temp.fargs)
                        except:
                            print("clients out of sink")
                    
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    self.running = False
                elif event.type == KEYDOWN:
                    if self.showChat:
                        try:
                            mods = pygame.key.get_mods()
                            if event.key == ord('/') and mods & pygame.KMOD_SHIFT:
                                self.ui.chatString+="?"
                            elif event.key == ord('1') and mods & pygame.KMOD_SHIFT:
                                self.ui.chatString+="!"
                            elif event.key == ord('9') and mods & pygame.KMOD_SHIFT:
                                self.ui.chatString+="("
                            elif event.key == ord('0') and mods & pygame.KMOD_SHIFT:
                                self.ui.chatString+=")"
                            elif event.key == ord('=') and mods & pygame.KMOD_SHIFT:
                                self.ui.chatString+="+"
                            elif event.key == ord(';') and mods & pygame.KMOD_SHIFT:
                                self.ui.chatString+=":"
                            elif chr(event.key) in Text.pos.keys():
                                self.ui.chatString+=chr(event.key)
                            elif event.key == 8:
                                self.ui.chatString=self.ui.chatString[:-1]
                            
                            elif event.key == ord(' '):
                                self.ui.chatString+=" "
                            elif event.key == 13:
                                self.client.inQueue.put(ChatMessage(self.name,self.name+": "+self.ui.chatString))
                                self.ui.chat.update("you: "+self.ui.chatString, self.showChat)
                                self.ui.chatString = ""
                            self.ui.textField.update(self.ui.chatString)
                        except:
                            pass
                        """ord('a') : lambda: setattr(self, 'trans', [self.trans[0]-.1,self.trans[1]]),
                        ord('d') : lambda: setattr(self, 'trans', [self.trans[0]+.1,self.trans[1]]),
                        ord('w') : lambda: setattr(self, 'trans', [self.trans[0],self.trans[1]+.1]),
                        ord('s') : lambda: setattr(self, 'trans', [self.trans[0],self.trans[1]-.1]),"""
                        #ord(' ') : lambda: self.endTurn(),
                    {
                        308 : lambda: setattr(self, 'altDown', True),
                        304 : lambda: setattr(self, 'shiftDown', True)
                        }.get(event.key, lambda: True)()
                elif event.type == KEYUP:
                    {   K_ESCAPE : lambda : setattr(self.ui, 'showMenu', not self.ui.showMenu),
                        308 : lambda: setattr(self, 'altDown', False),
                        304 : lambda: setattr(self, 'shiftDown', False)
                        }.get(event.key, lambda: True)()
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 2:
                        self.mouseDown = True
                    elif event.button == 4 or event.button == 5:
                        self.zoom = self.zoom/.90 if event.button == 4 else self.zoom*.90
                    elif event.button == 1:
                        pass
                    elif event.button == 3:
                        clickEvent = True
                        if self.selected and self.selected.occupant and not self.combiner:
                            clicked = None
                            click = self.convertPoint(pygame.mouse.get_pos())
                            for h in self.engine.grid.land:
                                if self.inCircle((h.centre), click, .09):
                                    clicked = h
                                    break
                            if clicked:
                                if self.engine.movePath(clicked, self.selected.occupant):
                                    self.client.inQueue.put(TurnData('applyMove', [clicked.number, self.selected.number]))
                                    self.selected = clicked
                                    self.path.path([])
                elif event.type == MOUSEBUTTONUP:
                    clickEvent = True
                    if event.button == 1 and self.shiftDown:
                        if self.selected and self.selected.occupant:
                            click = self.convertPoint(pygame.mouse.get_pos())
                            for h in self.engine.grid.land:
                                if self.inCircle((h.centre), click, .09) and h.village == self.selected.village and h.occupant:
                                    self.combiner = h
                                    break
                    elif event.button == 1:
                        buttonClick = self.ui.click(self.convertStaticPoint(pygame.mouse.get_pos()))
                        self.combiner = None
                        if not buttonClick:
                            click = self.convertPoint(pygame.mouse.get_pos())
                            for h in self.engine.grid.land:
                                if self.inCircle((h.centre), click, .09) and h.owner==self.player and self.engine.turn == self.player:
                                    self.selected = h
                                    break
                    elif event.button == 2:
                        self.mouseDown = False
                elif event.type == MOUSEMOTION:
                    self.ui.mouseOver(self.convertStaticPoint(pygame.mouse.get_pos()))
                    if self.mouseDown:
                        rel = event.rel
                        self.trans[0] += rel[0]*.003/self.zoom
                        self.trans[1] -= rel[1]*.003/self.zoom
                    if self.selected and self.selected.occupant and self.selected.occupant.moved == False:
                        click = self.convertPoint(pygame.mouse.get_pos())
                        clicked = None
                        for h in self.engine.grid.land:
                            if self.inCircle((h.centre), click, .09):
                                clicked = h
                                break
                        if clicked:
                            self.path.path(self.engine.grid.Astar(self.selected, clicked)[1:])
            if self.running:
                self.zoom = max(1, min(2.09, self.zoom))
                self.trans = [max(-0.8*self.zoom, min(0.8*self.zoom,self.trans[0])), max(-0.6*self.zoom, min(0.6*self.zoom, self.trans[1]))]
                
                glClear(GL_COLOR_BUFFER_BIT)
                glUniform2f(self.transloc,self.trans[0],self.trans[1])
                glUniform1f(self.zoomloc,self.zoom)
                glLineWidth(4*self.zoom)
                
                if clickEvent:
                    self.updateGridBuffers()
                    self.updateObjectBuffers()
                self.drawMap()
                if self.selected and self.selected.occupant and self.selected.occupant.moved == False and not self.combiner:
                    self.path.draw()
                if self.altDown:
                    for o in self.villageOverlays.values():
                        o.draw()
                elif self.selected and self.selected.village and self.selected.owner == self.player:
                    self.villageOverlays[self.selected.village].draw()

                glUniform2f(self.transloc,0,0)
                glUniform1f(self.zoomloc,1)
                self.ui.topBar.draw()
                self.ui.bottomBar.draw()
                self.ui.chatButton.draw()
                if self.showChat:
                    self.ui.chat.newMessages = 0
                    self.ui.chat.draw()
                    self.ui.textField.draw()
                if self.ui.showMenu:
                    self.ui.drawMenu()
                

                if self.engine.turn == self.player:
                    self.ui.endButton.draw()
                    if self.selected:
                        if self.selected.occupant and self.combiner and self.combiner.occupant:
                            self.ui.drawCombine()
                        elif self.selected.occupant:
                            self.ui.drawUnitUI()
                        elif self.selected.village.hex == self.selected:
                            self.ui.drawVillageUI()
                        elif self.selected.village:
                            self.ui.drawHexUI()
                
                
                self.mainClock.tick(30)
                pygame.display.flip()

    def inCircle(self,p1,p2,r):
        return math.sqrt(pow(p1[0]-p2[0],2)+pow(p1[1]-p2[1],2))<r

    def convertPoint(self, p):
        return ((p[0]/self.height*2 -(self.width/self.height))/self.zoom-self.trans[0], (-(p[1]/self.height)*2+1)/self.zoom-self.trans[1])

    def convertStaticPoint(self, p):
        return ((p[0]/self.height*2 -(self.width/self.height)), (-(p[1]/self.height)*2+1))

    def bindTexture(self, texture, repeat = False):
        texID = 0
        try:
            image = pygame.image.load(texture)
            textureData = pygame.image.tostring(image, "RGBA", 1)
            texID = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texID)
            glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA, image.get_width(), image.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData )
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
            if repeat:
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        except:
            print ("can't open the texture: %s"%(texture))
        return texID

    def save(self):
        Tk().withdraw()
        filename = filedialog.asksaveasfilename(initialdir="saves")
        if filename:
            with open(filename, 'wb') as f:
                pickle.dump(self.engine,f)
            print("saved")

    def load(self):
        Tk().withdraw()
        filename = filedialog.askopenfilename(initialdir="saves")
        if filename:
            with open(filename, 'rb') as f:
                self.engine = pickle.load(f)

            self.selected = None
            self.combiner = None
            self.ui.visible = 0
            #for consistency
            if self.engine.turn == self.player:
                self.beginTurn()
            self.villageOverlays = {v : Overlay(v.hex.centre[0], v.hex.centre[1]+.05, 0.2, 0.025, "w:"+str(v.wood)+"  g:"+str(v.gold), 0.015, [0.8,0.8,0.8,0.5]) for v in self.engine.players[self.player].villages}
            self.loadGridBuffers()
            self.updateGridBuffers()
            self.updateObjectBuffers()
            self.engine.Gui = self
            print("loaded")

#winning condition


                
