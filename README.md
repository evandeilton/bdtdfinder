# BDTD Research Agent & Reviewer

A Python library for automated research and systematic literature reviews using Brazil's Digital Library of Theses and Dissertations (BDTD).

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration: OpenRouter API](#configuration-openrouter-api)
- [Usage](#usage)
  - [Using the Graphical Interface](#using-the-graphical-interface)
  - [Systematic Review Example](#systematic-review-example)
- [Output Structure](#output-structure)
- [Core Components](#core-components)
  - [BDTDReviewer (Core Class)](#bdtdreviewer-core-class)
  - [BDTDCrawler](#bdtdcrawler)
  - [BDTDAgent](#bdtdagent)
  - [PDFDownloader](#pdfdownloader)
- [Dependencies](#dependencies)
- [Running the Test Script](#running-the-test-script)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This library streamlines the process of conducting systematic literature reviews on academic content from Brazil’s Digital Library of Theses and Dissertations (BDTD). It automatically searches, filters, downloads, and analyzes academic documents, then leverages the OpenRouter API with state-of-the-art large language models (LLMs) to generate comprehensive literature reviews.

---

## Features

- **Automated Search & Crawling:** Intelligent multi-page crawling of the BDTD database.
- **Content Analysis:** Extract metadata and plain text from academic webpages.
- **PDF Management:** Automated download, validation, and organization of PDFs.
- **Systematic Review Generation:** Generate detailed, evidence-based literature reviews using LLMs.
- **Configurable Output:** Fully configurable output directory to store all results.
- **User-Friendly Interface:** Streamlit-based UI for easy interaction and visualization of results.

---

## Installation

Clone the repository and install the package:

```bash
# Clone the repository
git clone https://github.com/evandeilton/bdtdonauta.git
cd bdtdonauta

# Install the package and its dependencies
pip install .
```

All necessary dependencies will be installed automatically.

---

## Configuration: OpenRouter API

This library uses the [OpenRouter API](https://openrouter.ai/) to generate literature reviews by interfacing with multiple LLMs. To configure:

1. **Create an Account & Obtain an API Key:**  
   Sign up at [OpenRouter](https://openrouter.ai/) and get your API key.

2. **Set the API Key as an Environment Variable:**  
   Create a `.env` file in the project root (if needed) and add:
   ```
   OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
   ```
   Replace `YOUR_OPENROUTER_API_KEY` with your actual key.

3. **Model Selection:**  
   The default model for generating reviews is `google/gemini-2.0-pro-exp-02-05:free`. You may override this by passing a different model name via the `model` argument.

---

## Usage

Before using the library, ensure that the `OPENROUTER_API_KEY` environment variable is set.

### Using the Graphical Interface

You have two options to run the graphical interface:

1. **Command Line Interface (CLI)**
   ```bash
   streamlit run src/bdtdfinder/BDTDUi.py
   ```

2. **Jupyter Notebook**
   ```python
   import streamlit as st
   from BDTDUi import create_ui
   
   # Create and display the UI in the notebook
   create_ui()
   ```

   Note: When running in a notebook, you'll need to have `streamlit` installed and may need the `streamlit-notebook` extension for optimal display.

### Systematic Review Example

Here is an example script for performing a systematic review:

```python
import os
from BDTDReviewer import BDTDReviewer

# Ensure the API key is set
if not os.environ.get("OPENROUTER_API_KEY"):
    raise EnvironmentError("OPENROUTER_API_KEY environment variable not set.")

# Create a BDTDReviewer instance with your parameters
reviewer = BDTDReviewer(
    theme="regressão beta",
    output_lang="pt-BR",
    max_pages=1,              # Maximum pages to crawl
    max_title_review=2,       # Maximum number of titles to process
    download_pdfs=False,      # Set to True to download PDFs
    scrape_text=True,         # Enable text scraping from webpages
    output_dir="results",     # Custom output directory
    debug=True,               # Enable debug mode for detailed logs
    model="google/gemini-2.0-pro-exp-02-05:free"
)

# Run the review process
output_file = reviewer.run()
print(f"Literature review saved in: {output_file}")
```

---

## Output Structure

After execution, the output directory (defined by `--output-dir` or the `output_dir` parameter) will contain:

```
results/
├── [PDF folders]          # Folders with PDFs (if download_pdfs=True)
├── results.csv            # Raw search results from BDTD
├── results_filtered.csv   # Filtered search results
├── results_page.csv       # Plain text content scraped from webpages
└── literature_review_<timestamp>.md   # Generated literature review in Markdown format
```

---

## Core Components

### BDTDReviewer (Core Class)

The **BDTDReviewer** class is the central orchestrator for the entire literature review process. It integrates various modules to perform the following tasks:

- **Crawling & Search:**  
  Initiates a search on BDTD via the **BDTDAgent** (which internally uses **BDTDCrawler**) to retrieve raw academic records.
  
- **PDF & Text Processing:**  
  Uses the **PDFDownloader** (when enabled) to download PDFs, and scrapes plain text content from webpages to extract relevant metadata.
  
- **Metadata Extraction:**  
  Sends extracted text to the OpenRouter API for metadata extraction using a predefined system prompt. The response is cleaned (removing markdown delimiters, etc.) and converted to a JSON dictionary.
  
- **Review Generation:**  
  Formats the extracted metadata into a prompt and calls the OpenRouter API again (using another detailed system prompt) to generate a comprehensive literature review.
  
- **Output Management:**  
  Manages an output directory (configurable via the `--output-dir` argument) by cleaning previous outputs and saving all generated files (CSV files, Markdown review, downloaded PDFs) in the same location.
  
**Key Attributes:**
- `theme`: The subject of the literature review.
- `output_lang`: Language in which the review will be generated.
- `max_pages`: Maximum pages to crawl on the BDTD.
- `max_title_review`: Maximum number of titles to process.
- `download_pdfs`: Flag to download PDF files.
- `scrape_text`: Flag to extract text from webpages.
- `output_dir`: Directory for all output files.
- `debug`: Flag to enable detailed debug logs.
- `model`: Specifies the LLM model to use.
- `openrouter_api_key`: API key for accessing OpenRouter services.

**Core Methods:**
- `_call_openrouter()`: Calls the OpenRouter API with provided prompts.
- `_extract_metadata()`: Extracts metadata from text using the OpenRouter API.
- `_generate_review()`: Generates the final literature review by formatting metadata and calling the API.
- `run()`: Coordinates the entire process—from cleaning the output directory, invoking the agent for crawling/scraping, to generating and saving the final review.

---

### BDTDCrawler

- **Purpose:** Crawls the BDTD database to search for theses and dissertations based on provided keywords.
- **Functions:**  
  - Constructs query URLs.
  - Fetches search results.
  - Processes and saves raw data to CSV.

---

### BDTDAgent

- **Purpose:** Integrates the crawling (via BDTDCrawler), filtering, PDF downloading (via PDFDownloader), and text scraping tasks.
- **Functions:**  
  - Executes multi-page searches.
  - Filters results by relevance.
  - Saves output files (CSV for raw results, filtered results, and page text).

---

### PDFDownloader

- **Purpose:** Locates and downloads PDF files from academic webpages.
- **Functions:**  
  - Follows URL redirects.
  - Downloads PDFs and saves them in a configurable directory.
  - Handles download errors gracefully.

---

## Dependencies

This library requires the following Python packages:

- `beautifulsoup4`: For web scraping
- `requests`: For making HTTP requests
- `openai`: For OpenAI API integration
- `python-dotenv`: For environment variable management
- `tiktoken`: For token counting
- `pandas`: For data manipulation
- `streamlit`: For the graphical user interface

Install these packages via pip:
```bash
pip install .
```

For the UI functionality, make sure to also install streamlit:
```bash
pip install streamlit
```

## Using the Graphical Interface
To start the graphical interface, run:
```bash
streamlit run src/bdtdfinder/BDTDUi.py
```

The UI provides:
- Easy configuration of search parameters
- Real-time progress tracking
- Interactive review visualization
- PDF management and download
- Configurable model selection for AI processing

---

## Running the Test Script

To run the provided test script:

1. Ensure the `OPENROUTER_API_KEY` environment variable is set.
2. Execute the test script:
   ```bash
   python test.py
   ```

---

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues to enhance functionality or fix bugs.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

By following these instructions, you can efficiently perform automated research and generate systematic literature reviews using the BDTD. Enjoy exploring and contributing to the project!

---
