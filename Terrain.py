from Obj3D import *

class Ground(Obj3D):
    def __init__(self, gameObj, model, renderParent=None, pos=None, hpr=None):
        super().__init__(model, renderParent, pos, hpr)
        self.gameObj = gameObj

        if model == "ground":
            self.setScale(scaleX=0.1, scaleY=0.02)

        self.move(dz=self.dimZ/2)

        args = {
            "padding": (0, 0, 0.01)
        }

        self.initSurroundingCollisionObj("floor", args=args, show=False)

        colNode = self.getCollisionNode("floor")
        colNode.node().setIntoCollideMask(self.gameObj.colBitMask["floor"])
        colNode.node().setFromCollideMask(self.gameObj.colBitMask["off"])

        # Make bottom extra big
        padZ = 10


class Terrain():
    def __init__(self, gameObj):
        self.gameObj = gameObj

        racetrack = self.gameObj.racetrack

        _, angles = racetrack.leftTrackPoints[0]
        pos = racetrack.points[0]

        self.startLine = Ground(self.gameObj, "cornfield", pos=pos)
        self.startLine.rotate(
            dh=angles[0], dp=angles[1])
