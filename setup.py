"""
Setup configuration for Airalo Python SDK.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="airalo-python-sdk",
    version="1.0.0",
    author="Airalo",
    author_email="developer@airalo.com",
    description="Python SDK for Airalo Partner API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Airalo/airalo-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.1",
    install_requires=[
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pylint>=3.0.0",
            "black>=23.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "mypy>=1.0.0",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/Airalo/airalo-python-sdk/issues",
        "Source": "https://github.com/Airalo/airalo-python-sdk",
        "Documentation": "https://github.com/Airalo/airalo-python-sdk#readme",
    },
)