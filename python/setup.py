"""Setup configuration for RAIL Score Python SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rail-score-sdk",
    version="2.1.0",
    author="Sumit Verma, Responsible AI Labs",
    author_email="sumit@responsibleailabs.ai",
    description="Official Python SDK for RAIL Score API - Responsible AI Content Evaluation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RAILethicsHub/rail-score/tree/main/python",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "httpx>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
            "types-requests>=2.28.0",
        ],
        "openai": ["openai>=1.0"],
        "anthropic": ["anthropic>=0.30"],
        "google": ["google-genai>=1.0"],
        "langfuse": ["langfuse>=3.0"],
        "litellm": ["litellm>=1.40"],
        "integrations": [
            "openai>=1.0",
            "anthropic>=0.30",
            "google-genai>=1.0",
            "langfuse>=3.0",
            "litellm>=1.40",
        ],
    },
    keywords=[
        "rail",
        "ai-ethics",
        "content-evaluation",
        "responsible-ai",
        "ai-safety",
        "content-moderation",
    ],
    project_urls={
        "Documentation": "https://responsibleailabs.ai/developer/docs",
        "API Reference": "https://responsibleailabs.ai/developers/api-ref",
        "Source": "https://github.com/RAILethicsHub/rail-score/tree/main/python",
        "Bug Reports": "https://github.com/RAILethicsHub/rail-score/issues",
        "Changelog": "https://github.com/RAILethicsHub/rail-score/blob/main/python/CHANGELOG.md",
    },
)
