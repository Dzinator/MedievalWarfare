import pygame, sys,math,  numpy as np, OpenGL.arrays.vbo as glvbo
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.raw import GL as g
from OpenGL.GL import shaders
from OpenGL.GLU import *
from ctypes import util
from OpenGL.arrays import ArrayDatatype as ADT

class Text:
    a = 0.125
    pos = {"0":(0,5),"1":(1,5),"2":(2,5),"3":(3,5),"4":(4,5),"5":(5,5),"6":(6,5),"7":(7,5),
           "8":(0,4),"9":(1,4),
           "a":(1,3),"b":(2,3),"c":(3,3),"d":(4,3),"e":(5,3),"f":(6,3),"g":(7,3),
           "h":(0,2),"i":(1,2),"j":(2,2),"k":(3,2),"l":(4,2),"m":(5,2),"n":(6,2),"o":(7,2),
           "p":(0,1),"q":(1,1),"r":(2,1),"s":(3,1),"t":(4,1),"u":(5,1),"v":(6,1),"w":(7,1),
           "x":(0,0),"y":(1,0),"z":(2,0), "!":(1,7), ":":(2,4)}
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
        self.changeText(text)
        

    def changeText(self,text):
        x = self.centre[0]
        y = self.centre[1]
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
            elif c!=" ":
                centres+=[x+size*n*2,y]*4
                p = self.pos[c]
                verts+=[[self.a*p[0],.065+self.a*p[1]],
                        [.045+self.a*p[0],.065+self.a*p[1]],
                        [.045+self.a*p[0],.125+self.a*p[1]],
                        [self.a*p[0],.125+self.a*p[1]]]
            n+=1

        self.text =text
        self.size = size
        
        self.length = len(centres)

        self.texVerts = glvbo.VBO(np.array(verts , dtype=np.float32))
        self.offsets = glvbo.VBO(np.array(centres, dtype=np.float32))

        self.vertices = glvbo.VBO(np.array([[-size,-size],[size,-size],[size,size],[-size,size]]*len(centres) , dtype=np.float32))

        off_data = np.array(centres, dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.offsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(off_data), ADT.voidDataPointer(off_data), GL_STREAM_DRAW)

        self.texVerts = np.array(verts, dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.texbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texVerts ), ADT.voidDataPointer(self.texVerts ), GL_STREAM_DRAW)
        
        g_tex_buffer_data = np.array([[-size,-size],[size,-size],[size,size],[-size,size]]*len(centres)  , dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), ADT.voidDataPointer(g_tex_buffer_data), GL_STREAM_DRAW)

        self.texoffVerts = np.array([0,0]*len(centres) , dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texoffVerts ), ADT.voidDataPointer(self.texoffVerts ), GL_STREAM_DRAW)

        colour_data = np.array(self.colour*4*len(centres) , dtype=np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.colorbuffer)
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

        glDrawArrays(GL_QUADS, 0, 4*self.length)

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

        self.texVerts = np.array(c*4 , dtype=np.float32)
        self.texbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.texbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, self.texbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texVerts ), ADT.voidDataPointer(self.texVerts ), GL_STATIC_DRAW)
        
        g_tex_buffer_data = np.array([[-w+x,-h+y],[w+x,-h+y],[w+x,h+y],[-w+x,h+y]] , dtype=np.float32)
        self.vertexbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.vertexbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_tex_buffer_data), ADT.voidDataPointer(g_tex_buffer_data), GL_STATIC_DRAW)

        self.texoffVerts = np.array([0,0,0,0]*4 , dtype=np.float32)
        self.texoffbuffer = g._types.GLuint(0)
        glGenBuffers(1, self.texoffbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, self.texoffbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(self.texoffVerts ), ADT.voidDataPointer(self.texoffVerts ), GL_STATIC_DRAW)

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
    def __init__(self, x, y, w, h, f, text):
        super().__init__(x,y,w,h,[.2,.2,.2,.999])
        self.clickFunction = f
       # self.image = bindTexture(image)
        self.text = Text(x-len(text)*0.014,y+0.005,0.015,text, [1,1,1,1])

    def inSquare(self, p):
        return (self.centre[0]+self.w>p[0]>self.centre[0]-self.w and self.centre[1]+self.h>p[1]>self.centre[1]-self.h)

    def click(self, p):
        if self.inSquare(p):
            self.clickFunction()

    def draw(self):
        super().draw()
        self.text.draw()

class UI:
    def __init__(self, gui):
        self.visible = 0
        self.gui = gui
        self.unitButtons = [Button(-1.6+i*.4,-.9,.13,.03, lambda: setattr(self.gui, 'show', not self.gui.show), t) for i,t in enumerate(["upgrade", "combine"])]
        self.villageButtons = [Button(-1.6+i*.4,-.9,.14,.03, lambda: setattr(self.gui, 'show', not self.gui.show), t) for i,t in enumerate(["upgrade", "purchase" ])]
        self.hexButtons = [Button(-1.4+i*.4,-.9,.18,.03, lambda: self.gui.selected.putTree(), t) for i,t in enumerate(["plant tree"])]

    def click(self, p):
        if self.visible ==1:
            for b in self.hexButtons:
                b.click(p)
        elif self.visible ==2:
            for b in self.unitButtons:
                b.click(p)
        elif self.visible ==3:
            for b in self.villageButtons:
                b.click(p)

    def drawHexUI(self):
        self.visible = 1
        for b in self.hexButtons:
            b.draw()

    def drawUnitUI(self):
        self.visible = 2
        for b in self.unitButtons:
            b.draw()

    def drawVillageUI(self):
        self.visible = 3
        for b in self.villageButtons:
            b.draw()

    def drawNone(self):
        self.visible = 0

class Overlay(Element):
    def __init__(self, x, y, w, h, text, size = 0.04, c = [.5,.5,.5,.9]):
        super().__init__(x,y,w,h,c)
        self.text = Text(x-w+size+0.01,y+h-size-0.01,size,text, [1,1,1,1])

    def draw(self):
        super().draw()
        self.text.draw()

class Gui:
    def __init__(self, engine, width, height):
        
        self.height = height
        self.width = width
        self.engine = engine
        self.mouseDown = False
        pygame.init()
        self.init()
        self.zoom = 1
        self.trans = [0,0]
        self.shader = self.shaders()
        self.selected = None
        self.spriteSheetCuts = (4,2)
        self.back = Element(.27,.6,2.05,1.6,[0,0,0,.99])

        self.mainClock = pygame.time.Clock()
        shaders.glUseProgram(self.shader)
        loc = glGetUniformLocation(self.shader,'lightPos')
        glUniform2f(loc,0,0)
        loc2 = glGetUniformLocation(self.shader,'engine')
        glUniform2f(loc2,0,0)
        loc3 = glGetUniformLocation(self.shader,'zoom')
        glUniform1f(loc3,1)
        self.running = True

        self.mapTex = self.bindTexture("texture2.png")

        Text.image = self.bindTexture("ExportedFont_Alpha.png")

        self.villageOverlays = [Overlay(v.hex.centre[0], v.hex.centre[1]+.05, 0.13, 0.025, "w:"+str(v.wood)+"  g:"+str(v.gold), 0.015, [0.8,0.8,0.8,0.5]) for v in self.engine.players[0].villages]

        self.show = False
        self.ui = UI(self)
        temp = [0,0,0,0]
        for h in self.engine.grid.hexes:
            if h.owner != 0:
                temp[h.owner-1]+=1
        self.text = Overlay(1,.6,0.35,0.2,"territories.player 1:"+str(temp[0])+".player 2:"+str(temp[1])+".player 3:"+str(temp[2])+".player 4:"+str(temp[3]))
        
        #grid
        self.initGridBuffers()

        #objects
        self.initObjectBuffers()
        

    def init(self):
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

        uniform vec2 lightPos;
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

        d = self.engine.grid.d
        point_data = np.array([[-d/2,-d*math.sin(math.pi/3)], 
                [d/2,-d*math.sin(math.pi/3)],
                [d,0],
                [d/2,d*math.sin(math.pi/3)], 
                [-d/2,d*math.sin(math.pi/3)], 
                [-d,0]],dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridvertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(point_data), ADT.voidDataPointer(point_data), GL_STATIC_DRAW)

        colour_data = np.array([1,1,1,1]*6, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridcolorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(colour_data), ADT.voidDataPointer(colour_data), GL_STATIC_DRAW)


        centres = [ h.centre for h in self.engine.grid.hexes]
        g_offset_buffer_data = np.array(centres, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_offset_buffer_data), ADT.voidDataPointer(g_offset_buffer_data), GL_STATIC_DRAW)

        texData = [[1/self.spriteSheetCuts[0]*(h[0]+.5),1/self.spriteSheetCuts[1]*(h[1]+.5)] for h in [[-.25,-.5*math.sin(math.pi/3)], 
                                            [.25,-.5*math.sin(math.pi/3)],
                                            [.5,0],
                                            [.25,.5*math.sin(math.pi/3)], 
                                            [-.25,.5*math.sin(math.pi/3)], 
                                            [-.5,0]
                                            ]]
        vert_data = np.array(texData, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridtexbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(vert_data), ADT.voidDataPointer(vert_data), GL_STATIC_DRAW)

        UVoffsets = [ [1/self.spriteSheetCuts[0],0] if h.hasTree else ([0,1/self.spriteSheetCuts[1]] if h.water else [0,0]) for h in self.engine.grid.hexes]
        g_UVoffset_buffer_data = np.array( UVoffsets, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_UVoffset_buffer_data), ADT.voidDataPointer(g_UVoffset_buffer_data), GL_STATIC_DRAW)

        d-=.02
        g_overlay_buffer_data = np.array([[-d/2,-d*math.sin(math.pi/3)], 
                [d/2,-d*math.sin(math.pi/3)],
                [d,0],
                [d/2,d*math.sin(math.pi/3)], 
                [-d/2,d*math.sin(math.pi/3)], 
                [-d,0]], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaybuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlay_buffer_data), ADT.voidDataPointer(g_overlay_buffer_data), GL_STATIC_DRAW)

        g_overlayColor_buffer_data = np.array([0,0,0,.6]*6, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycolorbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayColor_buffer_data), ADT.voidDataPointer(g_overlayColor_buffer_data), GL_STATIC_DRAW)
        
        #[0.94,0.156,0.184,0] if h.owner==1 else ([0.165,0.63,0.6,0] if h.owner ==2 else ([1,1,1,0] if h.owner == 3 else ([0.8, 0.8, 0.1,0] if h.owner == 4 else [0,0,0,0]))) 
        g_overlayCOffset_buffer_data = np.array([[0.6118, .0118, 0.2824, 0] if h.owner==1 else ([0.0314, 0.5882, 0.651, 0] if h.owner ==2 else ([0, 0.0196, 0.302,0] if h.owner == 3 else ([.8098,0.3784, 0.0196,0] if h.owner == 4 else [0,0,0,-.6])))  for h in self.engine.grid.hexes], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), ADT.voidDataPointer(g_overlayCOffset_buffer_data), GL_STATIC_DRAW)

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
        offset_array = [village.hex.centre for player in self.engine.players for village in player.villages]+[unit.hex.centre for player in self.engine.players for village in player.villages for unit in  village.units]
        self.nObjects = len(offset_array)
        offset_data =  np.array(offset_array, dtype=np.float32)
        texOff_data = np.array([[3/self.spriteSheetCuts[0],2/self.spriteSheetCuts[1]] for player in self.engine.players for village in player.villages]+[[0,0] for player in self.engine.players for village in player.villages for unit in  village.units], dtype=np.float32)
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

    def updateGridBuffers(self):
        #needs change
        g_UVoffset_buffer_data = np.array(  [ [1/self.spriteSheetCuts[0],0] if h.hasTree else ([0,1/self.spriteSheetCuts[1]] if h.water else [0,0]) for h in self.engine.grid.hexes], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.gridUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_UVoffset_buffer_data), None, GL_STREAM_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_UVoffset_buffer_data), ADT.voidDataPointer(g_UVoffset_buffer_data), GL_STREAM_DRAW)

        g_overlayCOffset_buffer_data = np.array([[1,0,0,0] if h == self.selected else 
                                                 ([0.6118, .0118, 0.2824, 0] if h.owner==1 else 
                                                 ([0.0314, 0.5882, 0.651, 0] if h.owner ==2 else
                                                  ([0, 0.0196, 0.302,0] if h.owner == 3 else
                                                   ([.8098,0.3784, 0.0196,0] if h.owner == 4 else
                                                    [0,0,0,-.6]))))  for h in self.engine.grid.hexes], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(g_overlayCOffset_buffer_data), ADT.voidDataPointer(g_overlayCOffset_buffer_data), GL_STATIC_DRAW)
        
    def updateObjectBuffers(self):
        offset_array = [village.hex.centre for player in self.engine.players for village in player.villages]+[unit.hex.centre for player in self.engine.players for village in player.villages for unit in  village.units]
        self.nObjects = len(offset_array)
        offset_data =  np.array(offset_array, dtype=np.float32)
        texOff_data = np.array([[0,0] for player in self.engine.players for village in player.villages]+[[0,0] for player in self.engine.players for village in player.villages for unit in  village.units], dtype=np.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitUVoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texOff_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(texOff_data), ADT.voidDataPointer(texOff_data), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.unitoffsetbuffer)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(offset_data), None, GL_STATIC_DRAW)
        glBufferData(GL_ARRAY_BUFFER, ADT.arrayByteCount(offset_data), ADT.voidDataPointer(offset_data), GL_STATIC_DRAW)

    def drawGrid(self):
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
        glEnableVertexAttribArray(5)
        glBindBuffer(GL_ARRAY_BUFFER, self.overlaycffsetbuffer)
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 0, None)

        glDrawArraysInstanced(GL_LINE_LOOP, 0, 6,len(self.engine.grid.hexes))

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

    def run(self):
        while self.running:
            events = False
            for event in pygame.event.get():
                events = True 
                if event.type == QUIT:
                    pygame.quit()
                    self.running = False
                if event.type == KEYUP and event.key == K_ESCAPE:
                    pygame.quit()
                    self.running = False
                if event.type == KEYUP and event.key == ord('z'):
                    self.zoom = 2 if self.zoom == 1 else 1
                    loc3 = glGetUniformLocation(self.shader,'zoom')
                    glUniform1f(loc3,self.zoom)
                    click = convertPoint(pygame.mouse.get_pos(),self) if self.zoom == 2 else [0,0]
                    loc2 = glGetUniformLocation(self.shader,'engine')
                    glUniform2f(loc2,-click[0],-click[1])
                if event.type == KEYDOWN:
                    {ord('a') : lambda: setattr(self, 'trans', [self.trans[0]-.1,self.trans[1]]),
                        ord('d') : lambda: setattr(self, 'trans', [self.trans[0]+.1,self.trans[1]]),
                        ord('w') : lambda: setattr(self, 'trans', [self.trans[0],self.trans[1]+.1]),
                        ord('s') : lambda: setattr(self, 'trans', [self.trans[0],self.trans[1]-.1])
                        }.get(event.key, lambda: True)()
                if event.type == KEYUP:
                    {ord('a') : lambda: False
                    }.get(event.key, lambda: True)() 
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 4 or event.button == 5:
                        self.zoom = self.zoom/.90 if event.button == 4 else self.zoom*.90
                        loc3 = glGetUniformLocation(self.shader,'zoom')
                        glUniform1f(loc3,self.zoom)
                    if event.button == 1:
                        self.mouseDown = True
                    if event.button == 3:
                        click = self.convertPoint(pygame.mouse.get_pos())
                        for h in self.engine.grid.hexes:
                            if self.inCircle((h.centre), click, .09):
                                self.selected = h
                                break
                if event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mouseDown = False
                        self.ui.click(self.convertStaticPoint(pygame.mouse.get_pos()))
                if event.type == MOUSEMOTION:
                    if self.mouseDown:
                        rel = event.rel
                        self.trans[0] += rel[0]*.003/self.zoom
                        self.trans[1] -= rel[1]*.003/self.zoom
            if self.running:
                if self.zoom<1:
                    self.zoom = 1
                if self.zoom>2.09:
                    self.zoom = 2.09
                #viewbox
                if self.trans[0]>0.8*self.zoom:
                    self.trans[0] = 0.8*self.zoom
                if self.trans[0]<-0.8*self.zoom:
                    self.trans[0] = -0.8*self.zoom
                if self.trans[1]>0.6*self.zoom:
                    self.trans[1] = 0.6*self.zoom
                if self.trans[1]<-0.6*self.zoom:
                    self.trans[1] = -0.6*self.zoom
                loc2 = glGetUniformLocation(self.shader,'engine')
                loc3 = glGetUniformLocation(self.shader,'zoom')
                glUniform2f(loc2,self.trans[0],self.trans[1])
                glUniform1f(loc3,self.zoom)
                glClear(GL_COLOR_BUFFER_BIT)
                self.back.draw()
                glLineWidth(4*self.zoom)

                self.updateGridBuffers()
                self.drawGrid()
                if self.selected and self.selected.village:
                    for o in self.villageOverlays:
                        o.draw()

                glUniform2f(loc2,0,0)
                glUniform1f(loc3,1)
                if self.selected:
                    if self.selected.village:
                        self.ui.drawVillageUI()
                    elif self.selected.occupant:
                        self.ui.drawUnitUI()
                    else:
                        self.ui.drawHexUI()
                if self.show:
                    self.text.draw()
                self.mainClock.tick(60)
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