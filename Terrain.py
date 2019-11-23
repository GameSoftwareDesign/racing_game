from Obj3D import *

class Scene(Obj3D):
    def __init__(self, gameObj, model, renderParent=None, pos=None, hpr=None):
        super().__init__(model, renderParent, pos, hpr)
        self.gameObj = gameObj

        self.scaleAll(1)
        self.move(dz=self.dimZ/2-self.offsetZ)

        args = {
            "padding": (0, 0, 0)
        }

        self.initSurroundingCollisionObj("wall", args=args, show=True)

class Terrain():
    def __init__(self, gameObj):
        self.gameObj = gameObj

        # Load floor/scene
        self.scene = Scene(self.gameObj, "cornfield")

        # Sky
        self.sky = Obj3D("FarmSky")
