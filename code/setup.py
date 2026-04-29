from setuptools import setup, find_packages

setup(
    name="Featurizer",
    version="0.1.0",
    author="Dmitrii Zelenskii",
    author_email="dz-zd@mail.ru",
    description="A slight modification of Connor Mayer and Robert Daland's code that learns features from segment classes.",
    long_description=open("../README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Viridianus/Featurizer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: BSD 3-Clause License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.2",
)
