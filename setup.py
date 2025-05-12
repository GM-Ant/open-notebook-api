from setuptools import setup, find_packages

setup(
    name="open-notebook",
    version="0.1.0",
    packages=find_packages(exclude=['tests', 'docs', 'scripts', 'examples']),  # Adjusted to find packages in the current directory
    include_package_data=True,
)
