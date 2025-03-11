"""安装脚本"""

from setuptools import setup, find_packages

setup(
    name="docker_manager",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "docker>=7.0.0",
        "typer[all]>=0.9.0",
        "colorlog>=6.7.0",
        "pyyaml>=6.0",
        "rich>=13.4.2",
        "python-dotenv>=1.0.0",
        "questionary>=2.0.0",
        "click>=8.0.0",
        "shellingham>=1.5.0",
        "croniter>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dm=docker_manager.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="Docker深度学习环境管理工具",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="docker, container, deep learning, management",
    url="https://github.com/yourusername/docker_manager",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/docker_manager/issues",
        "Documentation": "https://github.com/yourusername/docker_manager/wiki",
        "Source Code": "https://github.com/yourusername/docker_manager",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
) 