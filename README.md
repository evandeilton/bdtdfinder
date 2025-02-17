# BDTD Research Agent & Reviewer

A Python library for automated research and systematic literature review using Brazil's Digital Library of Theses and Dissertations (BDTD).

## Features

- **Automated Search**: Intelligent crawling of BDTD's database
- **Content Analysis**: Natural Language Processing for content extraction and analysis
- **PDF Management**: Automatic download and organization of PDFs
- **Systematic Review**: Generation of literature reviews using advanced text analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/evandeilton/bdtdfinder.git
cd bdtdfinder

# Install the package
pip install .
```

The dependencies will be automatically installed when you install the package.

## OpenRouter API

This library uses the OpenRouter API to generate literature reviews. OpenRouter is a service that allows you to access multiple large language models (LLMs) through a single API key.

To use this library, you need to create an account on [OpenRouter](https://openrouter.ai/) and obtain an API key. You can then set the `OPENROUTER_API_KEY` environment variable as described below.

You can find a list of available models on the [OpenRouter Models page](https://openrouter.ai/models). The `BDTDReviewer` class defaults to using the `google/gemini-2.0-pro-exp-02-05:free` model, but you can specify a different model by passing the `model` argument to the constructor.

## Usage

Before using the library, you need to set the `OPENROUTER_API_KEY` environment variable. You can do this by adding the following line to your `.env` file (create one if it doesn't exist in the project root):

```
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

Replace `YOUR_OPENROUTER_API_KEY` with your actual OpenRouter API key.

### Basic Search

```python
import os
from bdtdfinder.BDTDResearchAgent import BDTDAgent

# Get OpenRouter API key from environment variable
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
if not openrouter_api_key:
    print("Error: OPENROUTER_API_KEY environment variable not set.")
    exit()

agent = BDTDReviewer(
    theme="regressão beta",
    download_pdfs=True,
    scrape_text=True,
    max_pages=1,
    max_title_review=2,
    output_lang='pt-BR',
    output_dir="results",
)
agent.run()
```

### Systematic Review

```python
import os
from bdtdfinder.BDTDReviewer import BDTDReviewer

# Get OpenRouter API key from environment variable
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
if not openrouter_api_key:
    print("Error: OPENROUTER_API_KEY environment variable not set.")
    exit()

reviewer = BDTDReviewer(
    theme="your research theme",
    output_dir="output"
)
review = reviewer.run()
```

## Output Structure

```
output/
├── results.csv            # Raw search results
├── results_filtered.csv   # Filtered results
├── results_page.csv      # Page content analysis
└── literature_review.md  # Generated review
```

## Running the Test Script

To run the test script, follow these steps:

1.  Ensure that you have set the `OPENROUTER_API_KEY` environment variable as described above.
2.  Run the test script using the following command:

    ```bash
    python test.py
    ```

## Features in Detail

### Search & Crawling

- Multi-page crawling support
- Automated PDF detection and download
- Content scraping and text extraction

### Analysis

- Text clustering and topic modeling
- Sentiment analysis
- Temporal distribution analysis
- Keyword extraction
- Quality metrics calculation

### Review Generation

- Automated literature review generation
- Citation management
- Theme-based content organization
- Research gap identification

## Important Classes

### BDTDCrawler

The `BDTDCrawler` class is responsible for crawling the BDTD (Brazilian Digital Library of Theses and Dissertations) and extracting metadata from the search results. It provides methods for:

-   Creating query URLs based on search keywords and parameters.
-   Fetching search results from the BDTD API.
-   Processing the search results and extracting relevant information.
-   Saving the extracted data to a CSV file.

### PDFDownloader

The `PDFDownloader` class is responsible for downloading PDF files from the URLs extracted by the `BDTDCrawler`. It provides methods for:

-   Following redirects to get the final URL of a PDF file.
-   Downloading PDF files from a given URL.
-   Handling potential errors during the download process.

## Dependencies

The library depends on the following Python packages:

-   beautifulsoup4
-   requests
-   openai
-   python-dotenv
-   tiktoken
-   pandas

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
