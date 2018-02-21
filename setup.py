# http://peterdowns.com/posts/first-time-with-pypi.html
# from setuptools import setup, find_packages
from distutils.core import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='lyricsgenius',
    version='0.1',
    description='Download lyrics and metadata from Genius.com',
    long_description=README,
    classifiers=[
        'Programming Language :: Python', # TODO
    ],
    author='John W. Miller',
    author_email='john.w.millr@gmail.com',
    url='https://github.com/johnwmillr/lyricsgenius',
    download_url = "https://github.com/johnwmillr/LyricsGenius/archive/0.1.tar.gz",
    keywords='genius api music lyrics artists albums songs',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'lyricsgenius = lyricsgenius.__main__:main']
    },
)
