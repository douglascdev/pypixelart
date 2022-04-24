#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read()


setup(
    author="Douglas C.",
    author_email="douglasc.dev@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="A keyboard-centric approach to pixel art",
    entry_points={
        "console_scripts": [
            "pypixelart=pypixelart.main:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords=["pypixelart", "pygame", "image-editor", "pixel-art"],
    name="pypixelart",
    packages=find_packages(include=["pypixelart", "pypixelart.*"]),
    url="https://github.com/douglascdev/pypixelart",
    version="0.1.3",
    zip_safe=False,
)
