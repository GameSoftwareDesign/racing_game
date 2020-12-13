from setuptools import setup

setup(
    name = "Bunny Bunny",
    version = '0.1',
    author = '2020CAUTEAM25',
    opitons = {
        'build_apps': {
            'include_patterns':[
                'audio/UrbanStreet.mp3',
                'audio/spring.mp3',

                'img/startscreen.jpeg',

                'models/car_truck_blue.egg',
                'models/car_truck_blue.png',
                'models/concrete_crate.egg',
                'models/cornfield.egg',
                'models/ground.egg',
                'models/passenger_bunny.egg',

                'models/tex/concrete.png',
                'models/tex/WoodPlanksBareWindmillCap.png',

                'models/maps/bunnytx.tif',
                'models/maps/cornfieldTEXTURE01.tif',
                'models/maps/groundBMP_7_-_Default_CL.tif',
                'font.ttf',
            ],
            'gui_apps': {
                'racing_game':'Game.py'
            },
            'platforms': [
                'manylinux1_x86_64',
                'macos_10_6_x86_64',
                'win_amd64',
                'win32',
            ],
            'plugins': [
                'pandagl',
                'p3openal_audio',
            ],
        }
    }
)