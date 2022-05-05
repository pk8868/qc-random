import setuptools
import os

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

setuptools.setup(
    name = "qcrandom",
    version = "0.3-1",
    author = "Pawel Kromka, Jakub Wtorkiewicz",
    author_email = "pawel.kromka.05@onet.eu, kuba.wtorkiewicz@gmail.com",
    description = "qcrandom is a python library which provides easy way to generate random numbers on quantum computers.",
    long_description = long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pk8868/qc-random/",
    keywords=["python", "random", "quantum"],
    install_requires=["qiskit"],
    project_urls={
        "Bug Tracker": "https://github.com/pk8868/qc-random/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7"
)