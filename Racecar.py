from Obj3D import *
class Racecar(Obj3D):
    nRacecars = 0

    def __init__(self, gameObj, model, passenger=None, renderParent=None, pos=None, hpr=None):
        super().__init__("car_" + model, renderParent, pos, hpr)
        self.gameObj = gameObj

        self.initCarAndPassengerModels(model, passenger)

        if isinstance(self, DisplayCar):
            return 
        
        self.id = Racecar.nRacecars
        Racecar.nRacecars += 1

        # Speed
        self.defaultRotationSpeed = 1
        self.maxSpeed = 5
        self.maxSpeedBackwards = -3.5

        self.maxRotationSpeed = 5

        self.friction = 0.03
        self.accInc = self.friction + 0.005
        self.defaultRotationAcceleration = -0.1

        self.allowStaticTurning = False

        self.isCollidingWall = False

        self.currLap = 0
        self.passedCheckpoints = []

        self.setSpeed(0, 0)
        self.setAcceleration(0, 0)

        if hasattr(self.gameObj, "racetrack"):
            self.initOnRacetrack()

        self.initCollisions()

        self.initAudio()

    def initCarAndPassengerModels(self, carName=None, passengerName=None):
        self.repositionToCenter()
        self.move(dz=self.dimZ/2)

        # Add passenger
        self.personName ="bunny" if passengerName == None else passengerName
        self.passenger = Passenger(
            self.gameObj,
            self.personName, self.model
        )

        self.passenger.scaleAll(1)

        self.passenger.move(dx=self.relOffsetX,
                            dy=self.relOffsetY,
                            dz=self.relOffsetZ
                            )

    # Init 3D audio
    def initAudio(self):
        self.attachAudio("audio/spring.wav", loop=False,
                         volume=1.5, dropOffFactor=0.3)

    def getColNodeName(self, extras):
        return f"car_{self.id}_{extras}"

    def initCollisions(self):
        self.initSurroundingCollisionObj(self.getColNodeName("wall"), "capsule")

        colNode = self.getCollisionNode(self.getColNodeName("wall"))
        colNode.node().setFromCollideMask(self.gameObj.colBitMask["wall"])

        self.colPusher = CollisionHandlerPusher()

        # Credits to https://discourse.panda3d.org/t/collisions/58/7
        self.colPusher.addCollider(colNode, self.model, base.drive.node())

        self.colPusher.addInPattern('%fn-in-%in')
        self.colPusher.addInPattern('%fn-again-%in')
        self.colPusher.addOutPattern('%fn-out-%in')

        self.colPusher.setHorizontal(True)

        base.cTrav.addCollider(colNode, self.colPusher)

        # Collision Events
        colNodeName = self.getColNodeName("wall")

        self.gameObj.accept(f"{colNodeName}-in-wall", self.onCollideWall)
        self.gameObj.accept(f"{colNodeName}-again-wall", self.onCollideWall)
        self.gameObj.accept(f"{colNodeName}-out-wall", self.onExitWall)

        self.colLifter = CollisionHandlerFloor()
        self.colLifter.setMaxVelocity(10)

        floorRayNode = self.addCollisionNode("floorRay")
        floorRayNode.node().addSolid(CollisionRay(
            self.offsetX, self.offsetY, self.passenger.offsetZ + self.passenger.dimZ, 
            0, 0, -1
        ))
        floorRayNode.node().setFromCollideMask(self.gameObj.colBitMask["floor"])
        floorRayNode.node().setIntoCollideMask(0)

        self.colLifter.addCollider(floorRayNode, self.model)

        base.cTrav.addCollider(floorRayNode, self.colLifter)

        # Init Event
        self.colCheckpointEvent = CollisionHandlerEvent()

        self.colCheckpointEvent.addInPattern('%fn-in-%in')
        self.colCheckpointEvent.addAgainPattern('%fn-again-%in')
        self.colCheckpointEvent.addOutPattern('%fn-out-%in')

        fromBitmask = self.gameObj.colBitMask["checkpoint"]

        colSphere = CollisionSphere(self.relOffsetX, self.relOffsetY, self.relOffsetZ, self.dimZ/2)

        self.colCheckpointNode = Obj3D.createIsolatedCollisionObj(
            self.getColNodeName("checkpoint"), colSphere, parentNode=self.model,
            fromBitmask=fromBitmask, intoBitmask=self.gameObj.colBitMask["off"],
            show=False
        )

        # Collision Events
        colNodeName = self.getColNodeName("checkpoint")

        base.cTrav.addCollider(self.colCheckpointNode, self.colCheckpointEvent)

        self.gameObj.accept(f"{colNodeName}-in-checkpoint", self.onPassCheckpoint)
    
    def initOnRacetrack(self, order=None):
        if order == None: 
            order = self.id

        trackPoints = self.gameObj.racetrack.points

        startPos = LVector3f(trackPoints[0])
        dirVec = LVector3f(trackPoints[1]) - startPos
        dirVec.normalize()

        dist = (self.dimY + 2) * order

        pos = startPos + dirVec * dist 

        trackPoints = self.gameObj.racetrack.leftTrackPoints
        yawFacing = trackPoints[0][1][0]

        # Position setting
        x, y, z = pos
        self.setPos(x, y, z)

        # Rotate to face the closest checkpoint
        self.rotate(dh=yawFacing)
        self.currLap = 0

        self.passedCheckpoints = [0 for i in range(len(trackPoints))]
        self.passedCheckpoints[0] = 1 # the first checkpoint is always passed

        return

    # CHECKPOINTS
    def onPassCheckpoint(self, entry):
        checkpointID = entry.getIntoNodePath().getPythonTag("checkpointID")

        if self.passedCheckpoints[checkpointID-1] > self.passedCheckpoints[checkpointID]:
            if self.gameObj.printStatements:
                print(f"Car {self.id}: Passed checkpoint {checkpointID}")
            self.passedCheckpoints[checkpointID] += 1

        elif checkpointID == 0 and self.passedCheckpoints[0] == self.passedCheckpoints[-1]:
            self.currLap += 1
            self.passedCheckpoints[0] += 1 

            totalLaps = self.gameObj.totalLaps

            if self.currLap >= totalLaps:
                self.gameObj.gameOver(self)
            else:
                if self.gameObj.printStatements: print(f"Car {self.id}: Starting new lap {self.currLap} of {totalLaps}!")
        else:
            N = len(self.passedCheckpoints)
            if self.gameObj.printStatements: print(f"Car {self.id}: Need to pass checkpoint {(checkpointID+N-1)%N} first")

    def onCollideWall(self, entry):

        self.isCollidingWall = True
        self.setSpeed(0, 0)
        self.setAcceleration(0, 0)

        if not self.gameObj.sfxMuted:
            self.audio["audio/spring.wav"].play()
        
    def onExitWall(self, entry):
        self.isCollidingWall = False
        return

    def setSpeed(self, spd=None, rotSpd=None):
        if isNumber(spd):
            self.speed = min(max(spd, self.maxSpeedBackwards), self.maxSpeed)

        if isNumber(rotSpd):
            self.rotationSpeed = min(rotSpd, self.maxRotationSpeed)

    def setAcceleration(self, acc=None, rotAcc=None):
        if isNumber(acc):
            self.acceleration = acc

        if isNumber(rotAcc):
            self.rotationAcceleration = rotAcc

    def getSpeed(self):
        return self.speed

    def getAcceleration(self):
        return self.acceleration

    def getRotationSpeed(self):
        return self.rotationSpeed

    def getRotationAcceleration(self):
        return self.rotationAcceleration

    def incSpeed(self, dv=0, dw=0):
        self.setSpeed(self.speed + dv, self.rotationSpeed + dw)

    def incAcceleration(self, da=0, dalpha=0):
        self.setAcceleration(self.acceleration + da, self.rotationAcceleration + dalpha)

    def angleToPoint(self, point):
        x, y, _ = self.getPos()
        px, py, _ = point

        return rad2Deg(math.atan2(x-px, py-y))

    def distanceToPoint(self, point, xyOnly=False):
        x, y, z = self.getPos()
        px, py, pz = point

        squared = (px - x) ** 2 + (py - y) ** 2

        if not xyOnly:
            squared += (pz - z) ** 2

        return math.sqrt(squared)

    # Update movement
    def updateMovement(self):
        useSpeedBasedFriction = (self.speed == 0) or (self.acceleration > 1.5 * self.friction)
        if useSpeedBasedFriction:
            friction = -self.friction * self.speed
        else:
            if self.speed > 0:
                friction = -self.friction
            elif self.speed < 0:
                friction = self.friction

        self.incAcceleration(friction)

        prevSpeed = self.speed
        prevRotSpeed = self.rotationSpeed
        self.incSpeed(dv=self.acceleration, dw=self.rotationAcceleration)

        # Direction changed
        if not sameSign(prevSpeed, self.speed):
            self.setSpeed(spd=0)
            self.setAcceleration(acc=0)

        # Direction changed
        if not sameSign(prevRotSpeed, self.rotationSpeed):
            self.setSpeed(rotSpd=0)
            self.setAcceleration(acc=0, rotAcc=0)

        dirAngle, _, _ = self.getHpr()
        dirAngle *= -(math.pi/180)  # to rad

        dy = self.speed * math.cos(dirAngle)
        dx = self.speed * math.sin(dirAngle)

        self.move(dx=dx, dy=dy)
        self.rotate(dh=self.rotationSpeed)

        # Reset
        if self.checkBelowGround():
            print(f"Oops, car {self.id} fell below ground")
            self.initOnRacetrack(0)
            return

    def checkBelowGround(self):
        _, _, z = self.getPos()
        groundLevel = self.gameObj.racetrack.trackBounds["z"][0] - self.dimZ * 2

        return z < groundLevel

    # Controls
    def doDrive(self, direction="forwards"):
        accInc = self.accInc
        if direction in [ "backward", "backwards", "back", "reverse" ]:
            self.incAcceleration(-1 * accInc)
        else:
            self.incAcceleration(+1 * accInc)

    def doTurn(self, direction="left"):
        if self.speed == 0 and not self.allowStaticTurning:
            return

        if direction in [ "right", "clockwise", "cw" ]:
            _dir = -1 if self.speed >= 0 else +1 
        else: 
            _dir = +1 if self.speed >= 0 else -1

        rotSpd = _dir * self.defaultRotationSpeed
        rotAcc = _dir * self.defaultRotationAcceleration

        self.setSpeed(rotSpd=rotSpd)
        self.setAcceleration(acc=0, rotAcc=rotAcc)

class Passenger(Obj3D):
    def __init__(self, gameObj, model, renderParent=None, pos=None, hpr=None):
        super().__init__("passenger_" + model, renderParent, pos, hpr)
        self.gameObj = gameObj

class DisplayCar(Racecar) :
    pass
