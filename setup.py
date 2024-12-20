from setuptools import setup
import re


def derive_version() -> str:
    version = ''
    with open('discord/__init__.py') as f:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

    if not version:
        raise RuntimeError('version is not set')

    if version.endswith(('a', 'b', 'rc')):
        # append version identifier based on commit count
        try:
            import subprocess

            p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out:
                version += out.decode('utf-8').strip()
            p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out:
                version += '+g' + out.decode('utf-8').strip()
        except Exception:
            pass

    return version


setup(version=derive_version())
