from setuptools import find_packages, setup

setup(
    name="techforge-cli",
    version="1.0.0",
    description="Official CLI for TechForge module development",
    author="TechForge Team",
    packages=find_packages(),
    package_data={
        "techforge_cli": [
            "templates/**/*",
            "templates/**/.gitkeep",
        ],
    },
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1",
        "pyyaml>=6.0",
        "rich>=13.0",
        "jinja2>=3.1",
    ],
    entry_points={
        "console_scripts": [
            "techforge=techforge_cli.main:cli",
        ],
    },
)
