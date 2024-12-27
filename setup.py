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
        "include_files":["res","paks"]
        #'excludes': excludes,
        #   'zip_include_packages': zip_include_packages,
        #'build_exe': 'build_windows',
    }
}

setup(name='aims',
      version='0.6.1',
      description="Alphen's Isometric Subway Simulator",
      executables=executables,
      options=options)