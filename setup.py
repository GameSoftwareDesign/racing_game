from setuptools import setup

setup(
    name = "Bunny Bunny",
    version = '0.1',
    author = '2020CAUTEAM25',
    options = {
        'build_apps': {
            'include_patterns': [
                '**/*.wav',
                'img/*.jpeg',
                '**/*.jpg',
                '**/*.egg',
                '**/*.png',
                '**/*.tif',
                'font/*',
                '**/*.track'
            ],
            'gui_apps': {
                'Bunny Bunny':'Game.py',
            },
            'log_filename': '$USER_APPDATA/BunnyBunny/output.log',
            'log_append': False,
            'platforms': [
                'win_amd64',
            ],
            'plugins': [
                'pandagl',
                'p3openal_audio',
                'p3fmod_audio',
            ],
        }
    }
)