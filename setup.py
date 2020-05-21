import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pysvdrp",
    version="0.0.1",
    author="Manuel Reimer",
    author_email="manuel.reimer@gmx.de",
    description="Python library to control VDR via the SVDRP protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/M-Reimer/pysvdrp",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
