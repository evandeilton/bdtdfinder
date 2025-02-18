from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bdtdfinder",
    version="0.1.1",
    author="José Lopes",
    author_email="evandeilton@gmail.com",
    description="A library for crawling, downloading, and reviewing theses and dissertations from the BDTD.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/evandeilton/bdtdfinder",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "beautifulsoup4>=4.9.3",
        "requests>=2.25.1",
        "pandas>=1.2.0",
        "numpy>=1.19.0",
        "scikit-learn>=0.24.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0",
        "nltk>=3.6.0",
        "textblob>=0.15.3",
        "streamlit>=1.22.0",
        "python-dotenv>=0.19.0"
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'flake8>=3.9.0',
            'black>=21.5b2',
            'isort>=5.8.0',
            'mypy>=0.812',
        ],
        'notebook': [
            'ipykernel',
            'notebook',
            'jupyterlab'
        ]
    },
    entry_points={
        'console_scripts': [
            'bdtd-ui=bdtdfinder.BDTDUi:main',
        ],
    }
)