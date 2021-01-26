from setuptools import find_packages, setup

with open("ReadMe.md", encoding='utf-8') as readme:
    long_description = readme.read()

setup(name="icoc",
      version="1.0.8",
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
      install_requires=[
          "bidict",
          "dynaconf",
          "matplotlib",
          "openpyxl",
          "pdfrw",
          "python-can",
          "reportlab",
          "semantic_version",
          "windows-curses",
      ],
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
              'test-sth = mytoolit.test.production.sth:main',
              'test-stu = mytoolit.test.production.stu:main',
              'convert-base64-mac = mytoolit.scripts.base64:main',
              'convert-mac-base64 = mytoolit.scripts.mac:main',
          ]
      },
      tests_require=['nose'],
      test_suite='nose.collector')
