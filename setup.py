from setuptools import setup, find_packages
import os

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name="robot-pageobjects",
      install_requires=required,
      version="01.00.03",
      description="Robot Page Objects",
      author="Charles Hamel, Matt Plotner",
      author_email="charleshamel73@yahoo.com,mattplotner@gmail.com",
      platforms="Microsoft Windows",
      long_description="Page Object Pattern for Robot Framework",
      packages=find_packages(),
      include_package_data=True)
