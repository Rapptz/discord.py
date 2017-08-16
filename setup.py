from setuptools import setup
import re, os

on_rtd = os.getenv('READTHEDOCS') == 'True'

requirements = []
with open('requirements.txt') as f:
  requirements = f.read().splitlines()

if on_rtd:
  requirements.append('sphinxcontrib-napoleon')

version = ''
with open('discord/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

readme = ''
with open('README.md') as f:
    readme = f.read()

extras_require = {
    'voice': ['PyNaCl==1.0.1'],
}

setup(name='discord.py',
      author='Rapptz',
      url='https://github.com/Rapptz/discord.py',
      version=version,
      packages=['discord', 'discord.ext.commands'],
      license='MIT',
      description='A python wrapper for the Discord API',
      long_description=readme,
      include_package_data=True,
      install_requires=requirements,
      extras_require=extras_require,
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)
