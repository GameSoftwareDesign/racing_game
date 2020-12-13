from setuptools import setup

setup(
    name = "Bunny Bunny",
    version = '0.1',
    author = '2020CAUTEAM25',
    opitons = {
        'build_apps': {
            'include_patterns': [
                'audio/*.mp3',
                'img/*.jpeg',
                '**/*.egg',
                '**/*.png',
                '**/*.tif',
                'font/*'
            ],
            'gui_apps': {
                'racing_game':'Game.py',
            },
            'log_filename': '$USER_APPDATA/BunnyBunny/output.log',
            'log_append': False,
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