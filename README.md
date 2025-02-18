# BDTD Research Agent & Reviewer

**BDTD Research Agent & Reviewer** is a Python library for automating systematic literature reviews using Brazil's Digital Library of Theses and Dissertations (BDTD). It automates search, filtering, downloading, and analysis of academic documents and utilizes OpenRouter API with advanced LLMs to generate comprehensive reviews.

---

## Key Features

- **Automated Search & Crawling:**  
  - Intelligent multi-page crawling of BDTD.

- **Content Processing:**  
  - Extracts metadata and text from academic webpages.  
  - Automates PDF downloading and organization.

- **Review Generation:**  
  - Uses LLMs to generate detailed, evidence-based literature reviews.

- **Configurable Output:**  
  - Allows customization of the output directory and search parameters.

- **User Interface:**  
  - Provides a dedicated UI (Streamlit-based) for an interactive experience.

---

## Installation & Configuration

**Installation:**

1. Clone the repository and install the package:
   ```bash
   git clone https://github.com/evandeilton/bdtdfinder.git
   cd bdtdfinder
   pip install .
   ```
   
**OpenRouter API Configuration:**

- **Get an API Key:**  
  Create an account at [OpenRouter](https://openrouter.ai/) and retrieve your key.

- **Set the Environment Variable:**  
  Add it to a `.env` file (or directly in the environment):
  ```
  OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
  ```
  
- **Model Selection:**  
  The default model is `google/gemini-2.0-pro-exp-02-05:free`, but you can override it by specifying another model via the `model` parameter.

---

## Usage

Before running the library, ensure that the `OPENROUTER_API_KEY` environment variable is set.  
Here’s an example of performing a systematic review:

```python
import os
from bdtdfinder.BDTDReviewer import BDTDReviewer

# Check if the API key is set
if not os.environ.get("OPENROUTER_API_KEY"):
    raise EnvironmentError("OPENROUTER_API_KEY environment variable is not set.")

# Create an instance of BDTDReviewer with the desired parameters
reviewer = BDTDReviewer(
    theme="beta regression",
    output_lang="en-US",
    max_pages=1,              # Maximum pages to crawl
    max_title_review=2,       # Maximum number of titles to process
    download_pdfs=False,      # Set True to download PDFs
    scrape_text=True,         # Enable text extraction from webpages
    output_dir="results",     # Output directory
    debug=True,               # Debug mode for detailed logs
    model="google/gemini-2.0-pro-exp-02-05:free"
)

# Run the review process
output_file = reviewer.run()
print(f"Review saved in: {output_file}")
```

**Note on the UI:**  
The UI does not work in notebooks. Run it from the terminal using:
```bash
streamlit run /bdtdfinder/src/bdtdfinder/BDTDUi.py
```

---

## Output Structure & Core Components

**Output:**  
After execution, the output directory (e.g., `results/`) will contain:
- PDF folders (if `download_pdfs=True`)
- CSV files with raw and filtered search results
- A Markdown file with the generated literature review (timestamped)

**Core Components:**

- **BDTDReviewer:**  
  Orchestrates the entire process, from searching BDTD to generating the final review.

- **BDTDCrawler:**  
  Performs thesis and dissertation searches in BDTD.

- **BDTDAgent:**  
  Integrates crawling, filtering, PDF downloading, and text extraction.

- **PDFDownloader:**  
  Manages the downloading and organization of PDF files.

---

## Dependencies & Testing

**Required Dependencies:**
- beautifulsoup4
- requests
- openai
- python-dotenv
- tiktoken
- pandas

Install via pip if not already installed.

**Running the Test Script:**
```bash
python test.py
```

---

## Contributing & License

Contributions are welcome! Feel free to submit pull requests or open issues for enhancements or bug fixes.  
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Automate your research and generate systematic literature reviews efficiently! 🚀
