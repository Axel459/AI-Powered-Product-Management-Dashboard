from time import sleep
import requests
import pandas as pd
from bs4 import BeautifulSoup

def soup2list(src, list_, attr=None):
    """Helper function to extract data from BeautifulSoup results"""
    if attr:
        for val in src:
            try:
                list_.append(val[attr])
            except (KeyError, TypeError):
                list_.append(None)
    else:
        for val in src:
            try:
                list_.append(val.get_text().strip())
            except AttributeError:
                list_.append(None)

class InsufficientReviewsError(Exception):
    """Custom error for when there aren't enough reviews"""
    pass                

def scrape_trustpilot_reviews(company_url: str, max_pages: int = 4, min_reviews: int = 50) -> pd.DataFrame:
    """
    Scrape reviews from Trustpilot
    Args:
        company_url: Company domain (e.g., 'apple.com')
        max_pages: Number of pages to scrape (default 4)
        min_reviews: Minimum number of reviews required (default 50)
    Raises:
        Exception: If insufficient reviews are found
    """
    users = []
    ratings = []
    locations = []
    dates = []
    reviews = []

    try:
        for i in range(1, max_pages + 1):
            print(f"Scraping page {i}...")
            result = requests.get(f"https://www.trustpilot.com/review/{company_url}?page={i}")

            if result.status_code != 200:
                if i == 1:
                    raise Exception(f"Failed to find URL on Trustpilot, please use alternative URL or search for another company. Status code: {result.status_code}")
                break

            soup = BeautifulSoup(result.content, 'html.parser')

            # Extract data
            soup2list(
                soup.find_all('div', {'class': 'styles_reviewContent__44s_M'}),
                reviews
            )
            sleep(1)

        if not reviews:  # If no reviews were found
            raise Exception("No reviews found for this company")

        # Create DataFrame
        review_data = pd.DataFrame({
            'review': reviews
        })

        # Check if we have enough reviews
        if len(review_data) < min_reviews:
            raise InsufficientReviewsError(
                f"Found {len(review_data)} reviews, but {min_reviews} are required. "
                "Please try searching for an alternative URL on trustpilot.com or search for another company."
            )

        return review_data

    except Exception as e:
        if isinstance(e, InsufficientReviewsError):
            raise
        raise Exception(f"Error scraping reviews: {str(e)}")
