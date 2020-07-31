import os
import sys
from setuptools import setup, find_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')
def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.docusign',
      version='0.2.1',
      description="Python docassemble package for integrating with DocuSign",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Radiant Law, Theo Hamilton",
      author_email="alex.hamilton@radiantlaw.com",
      license='The MIT License (MIT)',
      url="https://github.com/radiant-law/docassemble-docusign",
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5'
      ],
      keywords="docassemble docusign development",
      project_urls={
        "Radiant Law": "https://radiantlaw.com",
        "Source": "https://github.com/radiant-law/docassemble-docusign",
      },
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=['PyJWT', 'requests'],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/docusign', package='docassemble.docusign'),
     )

