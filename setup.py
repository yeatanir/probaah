# ================================
# FILE: setup.py
# ================================

from setuptools import setup, find_packages

setup(
    name="probaah",
    version="1.0.0",
    description="Automated research workflow engine for computational chemistry",
    long_description="Where research flows naturally (প্ৰবাহ)",
    author="Anirban Pal",
    author_email="akp6421@psu.edu",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "pyyaml>=6.0",
        "paramiko>=3.0",
    ],
    entry_points={
        "console_scripts": [
            "probaah=cli.main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)