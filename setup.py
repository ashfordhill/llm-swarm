"""
Setup script for LLM Swarm.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="llm-swarm",
    version="0.1.0",
    description="Multi-Agent LLM Orchestration for Automated Codebase Generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="LLM Swarm Team",
    author_email="team@llmswarm.dev",
    url="https://github.com/your-username/llm-swarm",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "llm-swarm=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Artificial Intelligence",
    ],
    keywords="llm ai code-generation multi-agent orchestration",
    project_urls={
        "Bug Reports": "https://github.com/your-username/llm-swarm/issues",
        "Source": "https://github.com/your-username/llm-swarm",
        "Documentation": "https://github.com/your-username/llm-swarm/wiki",
    },
)