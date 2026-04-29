from setuptools import setup, find_packages

setup(
    name="Featurizer",
    version="0.1.0",
    author="Connor Mayer, Robert Daland",
    author_email="connor.joseph.mayer@gmail.com",
    description="A code that learns features from segment classes.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/connormayer/Featurizer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: BSD 3-Clause License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.2",
)
