"""安装脚本"""

from setuptools import setup, find_packages

setup(
    name="docker_manager",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "docker>=7.0.0",
        "typer>=0.9.0",
        "pyyaml>=6.0",
        "rich>=13.4.2",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "docker_manager=docker_manager.cli:app",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Docker镜像管理工具",
    keywords="docker, image, management",
    url="https://github.com/yourusername/docker_manager",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 