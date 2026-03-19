from setuptools import setup
from py2app.build_app import py2app
import sys
import os

# Read the current directory for assets
APP = ['merge_pdfs.py']

# Only include Logo files if they exist
DATA_FILES = []
if os.path.exists('Logo.png'):
    DATA_FILES.append('Logo.png')

# Check for icon files in order of preference
icon_file = None
if os.path.exists('Logo.icns'):
    icon_file = 'Logo.icns'
elif os.path.exists('Logo.png'):
    # Will need to convert PNG to ICNS first
    icon_file = None

OPTIONS = {
    'py2app': {
        'argv_emulation': False,
        'includes': ['tkinter', 'pypdf', 'PIL'],
        'packages': ['pypdf', 'PIL'],
        'strip': True,  # Remove debug symbols to reduce app size
        'prefer_ppc': False,
    }
}

# Add icon only if ICNS exist
if icon_file:
    OPTIONS['py2app']['iconfile'] = icon_file

setup(
    name='PDF Merger',
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=['py2app'],
    version='1.0.0',
    description='A simple and elegant PDF merging application for macOS',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/pdf-merger',
    license='MIT',
)
