from Obj3D import *
from Racecar import *
from Terrain import *


import copy

class Wall(Obj3D):
    def __init__(self, gameObj, model, renderParent=None, pos=None, hpr=None):
        super().__init__(model, renderParent, pos, hpr)
        self.gameObj = gameObj

        if "crate" in model: 
            self.scaleAll(0.01)

        self.initTexture("WoodPlanksBareWindmillCap.jpg")

        self.repositionToCenter()
        self.move(dz=self.dimZ/2)

        args = {
            "padding": (0, 0, 0)
        }

        self.initSurroundingCollisionObj("wall", args=args)
        
        colNode = self.getCollisionNode("wall")
        colNode.node().setIntoCollideMask(self.gameObj.colBitMask["wall"])

class HighWall():
    def __init__(self, racetrack, nWalls=1, wallType=None, pos=(0,0,0), angles=(0,0)):
        self.racetrack = racetrack
        self.wallType = self.racetrack.wallType if wallType == None else wallType

        self.nWalls = nWalls
        self.walls = []

        theta, phi = angles

        for i in range(self.nWalls):
            wall = Wall(self.racetrack.gameObj, self.wallType, pos=pos)
            dz = wall.dimZ * i

            wall.move(dz=dz)
            wall.rotate(dh=theta, dp=phi)

class Racetrack(Obj3D):
    def __init__(self, gameObj, trackName="test.track"):
        self.gameObj = gameObj
        self.wallType = "concrete_crate"

        tempWall = Wall(self.gameObj, self.wallType)
        self.wallDim = tempWall.getDimensions()
        self.wallOffset = tempWall.getOffset()
        tempWall.destroy()

        tempCar = Racecar(self.gameObj, "truck_blue")
        tempCarDim = tempCar.getDimensions()
        tempCar.destroy()
        Racecar.nRacecars -= 1

        # Set wall spacing (여기 곱하는거 늘리면 간격 넓어짐!)
        self.defaultWallSpacing = max(self.wallDim) + tempCarDim[0] * 12

        # Generate racetrack
        self.points = []
        self.trackBounds = {
            "x": [None, None],
            "y": [None, None],
            "z": [None, None]
        }
        self.generateRacetrackFromFile(trackName)
        self.getRacetrackBounds()

        # Generate checkpoints
        self.showCheckpoints = False
        self.checkpoints = []
        self.generateCheckpoints()

        return

    
    # Generate checkpoints
    def generateCheckpoints(self):
        leftTrackPoints = self.leftTrackPoints
        rightTrackPoints = self.rightTrackPoints

        checkPointRad = self.wallDim[1]

        for i in range(len(leftTrackPoints)):
            leftPos, _ = leftTrackPoints[i]
            rightPos, _ = rightTrackPoints[i]

            x0, y0, z0 = leftPos
            x1, y1, z1 = rightPos

            colBox = CollisionCapsule(
                (x0, y0, z0),
                (x1, y1, z1),
                checkPointRad
            )

            colNode = Obj3D.createIsolatedCollisionObj(
                "checkpoint", colBox, intoBitmask=self.gameObj.colBitMask["checkpoint"],
                show=self.showCheckpoints
            )

            colNode.setPythonTag("checkpointID", i)

        return

        return

    @staticmethod
    def parseTrackFile(fileName):
        points = []

        try:
            f = open(f"racetracks/{fileName}", "r")
        except:
            print(f"Racetrack {fileName} not found, defaulting to test.track")
            f = open(f"racetracks/test.track", "r")

        lineNo = 0
        for line in f:
            lineNo += 1
            line = re.sub(r"\#(.+)", "", line).strip()

            if len(line) == 0: 
                continue
            
            point = line.split(" ")
            if len(point) == 2:
                point.append(0)
            elif len(point) != 3:
                raise Exception(f"Invalid format in line {lineNo} of {fileName}.track")

            for i, coord in enumerate(point):
                try:
                    point[i] = float(coord)
                except:
                    raise Exception(f"Invalid format in line {lineNo} of {fileName}.track")

            points.append(tuple(point))

        if points[0] == points[-1]:
            points.pop()

        for i in range(len(points)-2, 0, -1):
            dir1 = LVector3f(points[i]) - LVector3f(points[i-1])
            dir2 = LVector3f(points[i]) - LVector3f(points[i+1])

            dir1.normalize()
            dir2.normalize()

            if dir1.cross(dir2) == LVector3f.zero():
                points.pop(i)

            continue

        if len(points) <= 3:
            raise Exception(f"{fileName}.track: Not enough points to make a racetrack!")

        f.close()
        return points

    def generateRacetrackFromFile(self, fileName):
        points = Racetrack.parseTrackFile(fileName)

        N = len(points)

        leftTrackPoints = []
        rightTrackPoints = []

        for i in range(N):

            point = points[i]

            dir1 = sub2Tuples(points[i-1], point)
            dir2 = sub2Tuples(points[(i+1) % N], point)

            p1a, p1b, _ = self.calculateSideTracks((point, dir1))
            p2b, p2a, angles = self.calculateSideTracks((point, dir2))

            sideLine1 = (p1a, dir1)
            sideLine2 = (p2a, dir2)
            pos = intersectionOfLines(sideLine1, sideLine2)

            leftTrackPoints.append((pos, angles))

            # Right track
            sideLine1 = (p1b, multiplyVectorByScalar(dir1, -1))
            sideLine2 = (p2b, multiplyVectorByScalar(dir2, -1))
            pos = intersectionOfLines(sideLine1, sideLine2)

            rightTrackPoints.append((pos, angles))

        for i in range(N):
            p0, angles = leftTrackPoints[i]
            p1, _ = leftTrackPoints[(i+1) % N]

            self.genWallsFromPointToPoint(p0, p1, angles)

            # Right Track
            p0, angles = rightTrackPoints[i]
            p1, _ = rightTrackPoints[(i+1) % N]

            self.genWallsFromPointToPoint(p0, p1, angles)

        self.points = points
        self.leftTrackPoints = leftTrackPoints
        self.rightTrackPoints = rightTrackPoints

        return
        
    def getRacetrackBounds(self):
        p0, _ = self.leftTrackPoints[0]
        x0, y0, z0 = p0

        self.trackBounds["x"] = (x0, x0)
        self.trackBounds["y"] = (y0, y0)
        self.trackBounds["z"] = (z0, z0)

        for i in range(len(self.leftTrackPoints)):
            p0, _ = self.leftTrackPoints[i]
            p1, _ = self.rightTrackPoints[i]

            x0, y0, z0 = p0
            x1, y1, z1 = p1

            self.trackBounds["x"] = (
                min(x0, x1, self.trackBounds["x"][0]), 
                max(x0, x1, self.trackBounds["x"][1])
            )
            self.trackBounds["y"] = (
                min(y0, y1, self.trackBounds["y"][0]),
                max(y0, y1, self.trackBounds["y"][1])
            )
            self.trackBounds["z"] = (
                min(z0, z1, self.trackBounds["z"][0]),
                max(z0, z1, self.trackBounds["z"][1])
            )

        return self.trackBounds

    def genWallsFromPointToPoint(self, startPoint, endPoint, angles=None):
        if angles == None: angles = (0, 0)
        theta, phi = angles

        directionVector = sub2Tuples(endPoint, startPoint)
        distance = getVectorMagnitude(directionVector)

        if distance == 0: return

        wallSize = self.wallDim[1]
        nWallsNeeded = math.ceil(distance / wallSize)

        for i in range(nWallsNeeded):
            pos = add2Tuples(
                startPoint, 
                multiplyVectorByScalar(directionVector, i * wallSize/distance)
            )
            wall = HighWall(self, nWalls=2, wallType=self.wallType, pos=pos, angles=angles)

            ground = Ground(self.gameObj, "ground", pos=pos)
            ground.rotate(dh=theta, dp=phi)


    def calculateSideTracks(self, line, spacing=0):
        startPos, directionVector = line

        spacing = self.defaultWallSpacing if (spacing == None or spacing <= 0) else spacing

        directionVector = normaliseVector(directionVector)
        if directionVector == (0, 0, 0): return

        x, y, z = startPos
        directionVector = multiplyVectorByScalar(directionVector, spacing/2)
        a, b, c = directionVector

        pos1 = x - b, y + a, z
        pos2 = x + b, y - a, z

        try:
            theta = radToDeg(math.atan2(-a, b))
        except:
            theta = 0 

        try:
            r = math.sqrt(a**2 + b**2)
            phi = radToDeg(math.atan(c/r))
        except:
            phi = 0
        return pos1, pos2, (theta, phi)
