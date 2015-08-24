from setuptools import setup
import re

requirements = [
  'ws4py',
  'requests'
]

version = ''
with open('discord/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

readme = ''
with open('README.md') as f:
    readme = f.read()

setup(name='discord.py',
      author='Rapptz',
      url='https://github.com/Rapptz/discord.py',
      version=version,
      packages=['discord'],
      license='MIT',
      description='A python wrapper for the Discord API',
      long_description=readme,
      include_package_data=True,
      install_requires=requirements,
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)
