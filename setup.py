from setuptools import setup, find_packages

setup(name='scmoplot',
      version='0.0.0',
      description=u"Module for plotting Scanning MOKE data",
      classifiers=[],
      keywords='',
      author=u"Julian Irwin",
      author_email='julian.irwin@gmail.com',
      url='https://github.com/UW-Physics-Rzchlab/scmoplot',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      setup_requires=[]
      )
