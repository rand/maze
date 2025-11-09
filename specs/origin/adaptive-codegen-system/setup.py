"""
Setup configuration for Adaptive Constraint-Based Code Generation System
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="adaptive-codegen-system",
    version="0.1.0",
    author="ACCS Development Team",
    author_email="contact@accs-project.org",
    description="Adaptive Constraint-Based Code Generation System using LLMs and llguidance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/adaptive-codegen-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-asyncio>=0.21.0",
            "pytest-benchmark>=4.0.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.0",
        ],
        "smt": [
            "z3-solver>=4.12.0",
        ],
        "diffusion": [
            "diffusers>=0.16.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "accs=adaptive_codegen.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "adaptive_codegen": [
            "grammars/*.lark",
            "configs/*.yaml",
            "templates/*.jinja2",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/adaptive-codegen-system/issues",
        "Source": "https://github.com/yourusername/adaptive-codegen-system",
        "Documentation": "https://accs-docs.readthedocs.io/",
    },
)
