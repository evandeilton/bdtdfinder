# BDTD Research Agent & Reviewer

A Python-based tool for automated research and systematic literature review using Brazil's Digital Library of Theses and Dissertations (BDTD).

## Features

- **Automated Search**: Intelligent crawling of BDTD's database
- **Content Analysis**: Natural Language Processing for content extraction and analysis
- **PDF Management**: Automatic download and organization of PDFs
- **Systematic Review**: Generation of literature reviews using advanced text analysis
- **Data Visualization**: Statistical analysis and visualization of research trends

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bdtdfinder.git
cd bdtdfinder

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Search

```python
from BDTDResearchAgent import BDTDAgent

agent = BDTDAgent(
    subject="your search topic",
    max_pages_limit=50,
    download_pdf=True
)
agent.run()
```

### Systematic Review

```python
from BDTDReviewer import EnhancedBDTDReviewer

reviewer = EnhancedBDTDReviewer(
    theme="your research theme",
    api_provider=your_api_provider,
    max_pages=50,
    download_pdfs=True
)
review = reviewer.run()
```

## Output Structure

```
output/
├── results.csv            # Raw search results
├── results_filtered.csv   # Filtered results
├── results_page.csv      # Page content analysis
├── literature_review.txt  # Generated review
└── visualizations/
    ├── temporal_distribution.png
    └── cluster_heatmap.png
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
