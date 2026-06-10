from setuptools import setup, find_packages

setup(
    name="techforge-sdk",
    version="1.0.0",
    description="Official SDK for TechForge module backends",
    author="TechForge Team",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "pyyaml>=6.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
