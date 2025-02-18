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
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "beautifulsoup4",
        "requests",
        "openai",
        "python-dotenv",
        "tiktoken",
        "pandas",
        "streamlit"
    ],
    extras_require={
        'notebook': [
            'ipykernel',
            'notebook',
            'streamlit>=1.22.0'
        ]
    },
    package_data={'bdtdfinder': ['py.typed']}
)