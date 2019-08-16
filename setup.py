import setuptools
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="docassemble-docusign",
    version="0.1",
    description="Python docassemble package for integrating with DocuSign",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/radiant-law/docassemble-docusign",
    author="Radiant Law, Theo Hamilton",
    author_email="alex.hamilton@radiantlaw.com",
    license='MIT',
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
        "Source": "https://github.com/radiant-law/docassemble-docusign"
    ,
    },
    packages=setuptools.find_packages(),
    install_requires=['requests', 'pyjwt'],
    python_requires='>=3'
)
