from distutils.core import setup
from glob import glob
import subprocess

# scripts = glob('scripts/*')
# command = ['git', 'describe', '--tags']
# version = subprocess.check_output(command).decode().strip()
version = 3.0.0

setup(name='segviz',
      version=version,
      author='Shuo Han',
      description='Show the image and label image overlay.',
      author_email='shuohanthu@gmail.com',
      url='https://github.com/shuohan/segviz',
      license='MIT',
      packages=['segviz'],
      install_requires=['numpy', 'scipy', 'Pillow', 'improc3d'],
      scripts=scripts,
      classifiers=['Programming Language :: Python :: 3',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent'])
