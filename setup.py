from setuptools import setup

setup(name='segmentation_visualization',
      version='2.1.2',
      description='Show the label image on top of the correspoing image',
      author='Shuo Han',
      author_email='shuohanthu@gmail.com',
      url='https://github.com/Shuo-Han/segmentation-visualization',
      license='MIT',
      packages=['segmentation_visualization'],
      install_requires=['nibabel', 'numpy', 'scipy', 'Pillow'],
      scripts=['bin/interact_image', 'bin/show_slices',
               'bin/create_checkerboard'])
