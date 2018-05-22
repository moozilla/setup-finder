import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="setup-finder",
    version="0.1.0",
    author="moozilla",
    author_email="moozilla@protonmail.com",
    description="Tools for finding Tetris setups.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moozilla/setup-finder",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Topic :: Games/Entertainment :: Puzzle Games",
    ),
    python_requires='~=3.4',
    entry_points={
        'console_scripts': ['setup-finder=setupfinder.find:main'],
    })
