from distutils.core import setup
from glob import glob
import subprocess

scripts = glob('scripts/*')
command = ['git', 'describe', '--tags']
version = subprocess.check_output(command).decode().strip()

setup(name='segmentation-visualization',
      version=version,
      author='Shuo Han',
      description='Show the label image on top of the correspoing image',
      author_email='shuohanthu@gmail.com',
      url='https://github.com/Shuo-Han/segmentation-visualization',
      license='MIT',
      packages=['segmentation_visualization'],
      install_requires=['nibabel', 'numpy', 'scipy', 'Pillow'],
      scripts=scripts)
