# coding: utf-8

from cx_Freeze import setup, Executable

executables = [Executable('main.py')]

excludes = []

includes = ["keyword","pygame","json","os","pathlib","contextlib","urllib"]

zip_include_packages = []#["pygame","json","os","pathlib","contextlib"]

options = {
    'build_exe': {
        'include_msvcr': True,
        'includes': includes,
        "include_files":["res","trains"]
        #'excludes': excludes,
        #   'zip_include_packages': zip_include_packages,
        #'build_exe': 'build_windows',
    }
}

setup(name='hello_world',
      version='0.4.3',
      description='Isometric Subway Simulator',
      executables=executables,
      options=options)