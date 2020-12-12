# Core imports
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase

import sys

from direct.task.Task import Task
from direct.gui.DirectGui import *
from Racetrack import *
from Terrain import *
from CameraController import *
from panda3d.core import loadPrcFileData

# Globally change window title name
gameTitle = "Bunny Bunny"
loadPrcFileData("", f"window-title {gameTitle}")

class Game(ShowBase):
    fonts = {}
    selectedTrack = "Hexagon.track"
    selectedCar = "truck_blue"
    selectedPassenger = "bunny"
    level = "medium"

    currentState = None

    def __init__(self):
        ShowBase.__init__(self)

        Game.fonts["Action_Man"] = loader.loadFont('font.ttf')

        self.nextState("start")

    def nextState(self, state):
        self.destroyInstance()

        state = state.lower().replace(" ", "")

        Game.currentState = state

        if state in [ "startscreen", "start" ]:
            StartScreen()
        elif state in [ "game", "racing", "racinggame", "main" ]:
            RacingGame()
        else:
            print(f"ERROR: State {state} not found")
            sys.exit()

    def destroyInstance(self):
        self.destroy()


class StartScreen(Game):
    def __init__(self):
        ShowBase.__init__(self)

        concreteBg = OnscreenImage(
            image="img/startscreen.jpeg",
            scale=(1.5, 1.5, 1)
        )

        title = OnscreenText(
            text=gameTitle, pos=(0, 0.5), scale=0.32,
            font=Game.fonts["Action_Man"],
            align=TextNode.ACenter, mayChange=False
        )

        startGameButton = DirectButton(
            text="Start  Game", text_font=Game.fonts["Action_Man"],
            scale=0.15, command=self.startGame,
            pad=(0.3, 0.3),
            pos=(0, 0, -0.7)
        )

        # Next frame without clicking
        self.accept("space-up", self.startGame)

    def startGame(self):
        self.nextState("game")


class RacingGame(Game):
    def __init__(self):
        ShowBase.__init__(self)

        # Get other stuff ready
        self.paused = False
        self.muted = False
        self.sfxMuted = False
        self.isGameOver = False
        self.gameOverTime = 0 # for camera rotation
        self.printStatements = False


        self.totalLaps = 1

        Obj3D.worldRenderer = self.render

        # Generate texts
        self.texts = {}

        # Load collision handlers
        self.collisionSetup(showCollisions=False)

        self.loadAudio()
        self.loadModels()
        self.loadBackground()
        self.loadLights()

        # Key movement
        self.isKeyDown = {}
        self.createKeyControls()

        # Init camera
        self.camConfigDefault = "perspective"
        self.camConfig = self.camConfigDefault
        self.taskMgr.add(self.setCameraToPlayer, "SetCameraToPlayer")
        self.taskMgr.add(self.keyPressHandler, "KeyPressHandler")
        self.taskMgr.add(self.gameTimer, "GameTimer")


    def setCameraToPlayer(self, task):
        # Focus on winning car when gameover
        player = self.player \
            if not self.isGameOver else self.winningCar

        x, y, z = player.getPos()
        h, p, r = player.getHpr()

        # Offset centers
        x += player.offsetX
        y += player.offsetY
        z += player.offsetZ

        camDistance = player.dimY * 1.5

        # Allow for variable camera configuration
        theta = degToRad(h)

        if "_rotate" in self.camConfig:
            if self.isGameOver and self.gameOverTime == 0:
                self.gameOverTime = task.time

            theta = (task.time - self.gameOverTime) * 2.5 + degToRad(h)

            # Stop rotation after n rotations
            nRotations = 1
            if self.isGameOver and theta - degToRad(h) >= ( (nRotations-1) * 2 * math.pi + math.pi):
                self.setCameraView("perspective_behind_win")
                self.pauseAudio()

        if "_behind" in self.camConfig:
            theta = degToRad(h - 180)

        camHeight = player.dimZ * 1.7
        xOffset = camDistance * math.sin(theta)
        yOffset = -camDistance * math.cos(theta)

        self.camera.setPos(x + xOffset, y + yOffset, z + camHeight)

        if "perspective" in self.camConfig:
            perspectiveOffset = 10
            xOffset = perspectiveOffset * math.sin(-theta)
            yOffset = perspectiveOffset * math.cos(-theta)
            self.camera.lookAt(x + xOffset, y + yOffset, z)

        if "_rotate" in self.camConfig:
            self.camera.lookAt(x, y, z)

        return Task.cont

    # Game over handling
    def gameOver(self, car):
        self.isGameOver = True
        self.winningCar = car

        if car.id == 0: # player
            winMsg = f"You are Winner!"

        self.texts["gameOver"] = OnscreenText(
            text=winMsg, pos=(0, 0.8), scale=0.15,
            bg=(255, 255, 255, 0.7), wordwrap=20,
            font=Game.fonts["Action_Man"],
            align=TextNode.ACenter, mayChange=False
        )

        startGameButton = DirectButton(
            text="Restart Game", text_font=Game.fonts["Action_Man"],
            scale=0.15, command=self.restartGame,
            pad=(0.3, 0.3),
            pos=(0, 0, -0.75)
        )

        # Make camera move and have the audio stop after
        self.setCameraView("perspective_rotate_win")
        return

    # Game Timer
    def gameTimer(self, task):
        if self.paused or self.isGameOver:
            return Task.cont

        for car in self.cars:
            car.updateMovement()

        return Task.cont

    # Load Audio
    def loadAudio(self):
        audio3d = Audio3DManager.Audio3DManager(
            base.sfxManagerList[0], base.camera
        )
        Obj3D.audio3d = audio3d

        self.audio = {}

        # Bg audio
        bgAudio = base.loader.loadSfx("audio/UrbanStreet.mp3")
        bgAudio.setLoop(True)
        bgAudio.setVolume(0.05)

        bgAudio.play()

        self.audio["bg"] = bgAudio

    # Load lights
    def loadLights(self):
        #add one light per face, so each face is nicely illuminated
        plight1 = PointLight('plight')
        plight1.setColor(VBase4(1, 1, 1, 1))
        plight1NodePath = render.attachNewNode(plight1)
        plight1NodePath.setPos(0, 0, 500)
        render.setLight(plight1NodePath)

        plight2 = PointLight('plight')
        plight2.setColor(VBase4(1, 1, 1, 1))
        plight2NodePath = render.attachNewNode(plight2)
        plight2NodePath.setPos(0, 0, -500)
        render.setLight(plight2NodePath)

        plight3 = PointLight('plight')
        plight3.setColor(VBase4(1, 1, 1, 1))
        plight3NodePath = render.attachNewNode(plight3)
        plight3NodePath.setPos(0, -500, 0)
        render.setLight(plight3NodePath)

        plight4 = PointLight('plight')
        plight4.setColor(VBase4(1, 1, 1, 1))
        plight4NodePath = render.attachNewNode(plight4)
        plight4NodePath.setPos(0, 500, 0)
        render.setLight(plight4NodePath)

        plight5 = PointLight('plight')
        plight5.setColor(VBase4(1, 1, 1, 1))
        plight5NodePath = render.attachNewNode(plight5)
        plight5NodePath.setPos(500, 0, 0)
        render.setLight(plight5NodePath)

        plight6 = PointLight('plight')
        plight6.setColor(VBase4(1, 1, 1, 1))
        plight6NodePath = render.attachNewNode(plight6)
        plight6NodePath.setPos(-500, 0, 0)
        render.setLight(plight6NodePath)

    def loadBackground(self):
        self.terrain = Terrain(self)

    def loadModels(self):
        self.cars = []
        Racecar.nRacecars = 0
        self.racetrack = Racetrack(self, Game.selectedTrack)
        self.player = Racecar(self, Game.selectedCar, Game.selectedPassenger, self.render)
        self.cars.append(self.player)
        if self.printStatements: print(f"Opponent cars generated with difficulty {Game.level}")

    # Key Events
    def createKeyControls(self):
        # Create a function to key maps
        # "<function>": [ <list of key ids> ]
        functionToKeys = {
            "forward": [ "arrow_up" ],
            "backward": [ "arrow_down"],
            "turnLeft": [ "arrow_left"],
            "turnRight": [ "arrow_right" ],
        }

        for fn in functionToKeys:
            keys = functionToKeys[fn]

            # Initialise dictionary
            self.isKeyDown[fn] = 0

            for key in keys:
                # Key Down
                self.accept(key, self.setKeyDown, [fn, 1])
                # Key Up
                self.accept(key+"-up", self.setKeyDown, [fn, -1])


    # Key Down 
    def setKeyDown(self, key, value):
        self.isKeyDown[key] += value
        if self.isKeyDown[key] < 0:
            self.isKeyDown[key] = 0

    def setCameraView(self, view):
        # Once win, only allow for win camera view
        if self.isGameOver and "_win" not in view:
            return

        self.camConfig = view
        if self.printStatements: print("Camera view set to: " + self.camConfig)

    def keyPressHandler(self, task):
        if self.paused or self.isGameOver:
            return Task.cont

        player = self.player

        if self.isKeyDown["forward"] > 0:
            player.doDrive("forward")

        if self.isKeyDown["backward"] > 0:
            player.doDrive("backward")

        if self.isKeyDown["turnLeft"] > 0:
            player.doTurn("left")

        if self.isKeyDown["turnRight"] > 0:
            player.doTurn("right")


        return Task.cont

    # Collision Events
    def collisionSetup(self, showCollisions=False):
        base.cTrav = CollisionTraverser()

        if showCollisions:
            base.cTrav.showCollisions(render)
           #gameOver(self,self.player)

        # Set bitmasks
        # Reference: https://www.panda3d.org/manual/?ti
        # tle=Bitmask_Examplexf
        self.colBitMask = {
            "off": BitMask32.allOff(),
            "wall": BitMask32.bit(0),
            "floor": BitMask32.bit(1),
            "checkpoint": BitMask32.bit(2),
            "offworld": BitMask32.bit(4)
        }

    # Toggle whether or not to print statements (for debugging or extra information)
    def togglePrintStatements(self):
        self.printStatements ^= True
        print("Printing Debug Statements:", self.printStatements)

    def togglePause(self, showHelp=True):
        self.paused ^= True
        self.pauseAudio()

        if showHelp:
            self.helpDialog.toggleVisible()

    def toggleMute(self):
        self.muted ^= True
        self.sfxMuted ^= True
        self.pauseAudio()
        return

    def pauseAudio(self):
        # We need to pause music too
        for nm in self.audio:
            sound = self.audio[nm]

            playRate = 0 if self.paused or self.isGameOver or self.muted else 1
            sound.setPlayRate(playRate)

    def restartGame(self):
        self.nextState("start")

game = Game()
game.run()