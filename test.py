import os
from bdtdfinder.BDTDResearchAgent import BDTDAgent
from bdtdfinder.BDTDReviewer import BDTDReviewer


# To run this test, you need to set the OPENROUTER_API_KEY environment variable.
# You can do this by adding the following line to your .env file:
# OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
# Replace YOUR_OPENROUTER_API_KEY with your actual OpenRouter API key.

def main():
    # Get OpenRouter API key from environment variable
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please set the OPENROUTER_API_KEY environment variable and try again.")
        return

    agent = BDTDReviewer(
        theme="regressão kumaraswamy",
        download_pdfs=True,
        scrape_text=True,
        max_pages=1,
        max_title_review=5,
        output_lang='en-US',
        output_dir="results",
    )
    agent.run()

if __name__ == "__main__":
    main()