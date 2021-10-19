from platform import system
from re import MULTILINE, search
from setuptools import find_packages, setup

with open("mytoolit/__init__.py", "r") as init_file:
    version = search(r"__version__\s*=\s*['\"](?P<version>[^'\"]*)['\"]",
                     init_file.read(),
                     flags=MULTILINE)['version']

with open("ReadMe.md", encoding='utf-8') as readme:
    long_description = readme.read()

required_packages = [
    "bidict",
    "dynaconf",
    "matplotlib",
    "netaddr",
    "openpyxl",
    "pdfrw",
    "python-can",
    "reportlab",
    "tables>=3.6",
    "semantic_version",
]

if system() == "Windows":
    required_packages.append("windows-curses")

setup(name="icoc",
      version=version,
      description=("Control and test software for sensory tool holders (STH) "
                   "and stationary transceiver units (STU)"),
      long_description=long_description,
      long_description_content_type="text/markdown",
      keywords="smart-tool stu sth tool-holder",
      author="MyTooliT",
      author_email="rene.schwaiger@ift.at",
      url="https://github.com/MyTooliT/ICOc",
      project_urls={
          'Documentation': "http://mytoolit.github.io/Documentation",
          'Source': "https://github.com/MyTooliT/ICOc",
      },
      packages=find_packages(),
      install_requires=required_packages,
      include_package_data=True,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3",
          "License :: Other/Proprietary License",
          "Operating System :: Microsoft :: Windows :: Windows 10",
      ],
      python_requires='>=3.7',
      entry_points={
          'console_scripts': [
              'icoc = mytoolit.old.mwt:main',
              'check-eeprom = mytoolit.scripts.eeprom:main',
              'clean-repo = mytoolit.scripts.clean:main',
              'test-sth = mytoolit.test.production.sth:main',
              'test-sth-verification = mytoolit.old.test.MyToolItTestSth:main',
              'test-stu = mytoolit.test.production.stu:main',
              'convert-base64-mac = mytoolit.scripts.name:main',
              'convert-mac-base64 = mytoolit.scripts.mac:main',
          ]
      })
