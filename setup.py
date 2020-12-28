import os
from glob import glob
from setuptools import setup, find_packages

dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(dir, 'README.md')) as f:
    long_description = f.read()

setup(name='segviz',
      version='3.1.1',
      author='Shuo Han',
      description='Show the image and label image overlay.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author_email='shuohanthu@gmail.com',
      url='https://github.com/shuohan/segviz',
      license='MIT',
      packages=find_packages(),
      install_requires=['numpy', 'scipy', 'Pillow', 'improc3d', 'jinja2',
                        'flask', 'nibabel'],
      python_requires='>=3.7',
      include_package_data=True,
      scripts=glob('scripts/*'),
      classifiers=['Programming Language :: Python :: 3',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent'])
