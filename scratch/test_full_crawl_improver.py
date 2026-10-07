import sys
sys.path.insert(0, '.')
import json
from utils import fetch_url
from bs4 import BeautifulSoup
import re
from optimizer import clean_seo_slug, estimate_pixel_width, generate_word_diff

def run_test():
    url = "https://www.inersialab.com/Programmes"
    notice = """- Focus keyword not found in the URL permalink
- Focus Keyword does not appear in the first 10% of the content.
- Use Focus Keyword in subheadings like H2, H3.
- Content is 220 words long. Consider using at least 600 words.
- Add a number to your SEO title to improve CTR.
- Add an emotional power word to your SEO title."""

    # Notice parser test
    # Verify keyword is NOT "to the SEO title" or "not found in the URL permalink"
    print("Testing URL:", url)

if __name__ == "__main__":
    run_test()
