import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
import json
from typing import Literal
import re

class PMCSearcher:
    def __init__(self, email=None, api_key=None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = email  # Required for courtesy
        self.api_key = api_key  # Optional, increases rate limits

    def search(self, query: str, max_results: int = 100) -> list[str]:
        pmids = self.get_pmids(query=query, max_results=max_results)
        articles = self.get_article_details(pmids=pmids)
        return articles

    def get_pmids(self, query: str, max_results: int = 100) -> list[str]:
        """
        Search with NCBI E-Utilities for articles matching query
        
        Parameters
        ----------
        query : str
            Search term to query NCBI PMC database
        max_results : int
            Maximum number of results to return (default 100)
        
        Returns
        -------
        list[str]
            List of PMIDs matching the search query
        """
        url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pmc',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        if self.email:
            params['email'] = self.email
        if self.api_key:
            params['api_key'] = self.api_key
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data['esearchresult']['idlist']

    def get_article_details(self, pmids: list[str]) -> list[dict]:
        """
        Get detailed information for list of PMIDs.

        Parameters
        ----------
        pmids : list[str]
            List of PMIDs to retrieve details for

        Returns
        -------
        list[dict]
            List of dictionaries containing article details
        """
        if isinstance(pmids, str):
            pmids = [pmids]
            
        url = f"{self.base_url}efetch.fcgi"
        params = {
            'db': 'pmc',
            'id': ','.join(pmids),
            'retmode': 'xml',
        }
        
        if self.email:
            params['email'] = self.email
        if self.api_key:
            params['api_key'] = self.api_key
            
        response = requests.get(url, params=params)
        response.raise_for_status()

        return self.parse_xml(response.text)
    
    def parse_xml(self, xml_text: str) -> list[dict]:
        """
        Parse XML response into structured data.

        Parameters
        ----------
        xml_text : str
            Raw XML text from response

        Returns
        -------
        list[dict]
            List of dictionaries containing article details
        """
        root = ET.fromstring(xml_text)
        articles = []
        
        for article in root.findall('.//article'):
            article_data = {
                'pmid': self._extract_pmid(article),
                'title': self._extract_title(article),
                'doi': self._extract_doi(article),
                'full_text': self._extract_full_text(article),
            }
            
            articles.append(article_data)
                
        return articles
    
    def _extract_pmid(self, article_elem: ET.Element) -> str:
        """
        Extract PMID from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            PMID or None if not found
        """
        for article_id in article_elem.findall('.//article-id'):
            if article_id.get('pub-id-type') == 'pmcaid':
                return article_id.text
        return None
    
    def _extract_title(self, article_elem: ET.Element) -> str:
        """
        Extract article title from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            Article title or "No title" if not found
        """
        title_elem = article_elem.find('.//article-title')
        return title_elem.text if title_elem is not None else "No title"
    
    def _extract_doi(self, article_elem: ET.Element) -> str:
        """
        Extract DOI from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            DOI or None if not found
        """
        for article_id in article_elem.findall('.//article-id'):
            if article_id.get('pub-id-type') == 'doi':
                return article_id.text
        return None
    
    def _extract_full_text(self, article_elem: ET.Element) -> str:
        """
        Extract full text content from the article element.

        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            The full text content of the article
        """
        return ''.join(article_elem.itertext()).strip()

def search_dandi_articles(verbose: bool = False) -> list[dict]:
    # Initialize API (replace with your email)
    searcher = PMCSearcher(email="paul.wesley.adkisson@gmail.com")

    # Search queries for DANDI-related articles
    queries = [
        '"DANDI Archive"',
        '"Distributed Archives for Neurophysiology Data Integration"',
    ]
    all_articles = []

    if verbose:
        print(f"Searching PMC for DANDI-related articles...")
    for query in queries:
        if verbose:
            print(f"Querying PMC with: {query}")
        articles = searcher.search(query=query, max_results=100)
        all_articles.extend(articles)
        # Rate limiting - be nice to NCBI servers
        time.sleep(1)
    
    return all_articles

def extract_dandisets_from_articles(articles):
    """
    For each article, search the full_text (if present) for Dandiset IDs or URLs.

    The Dandiset ID can be in various formats:
    - https://dandiarchive.org/dandiset/123456
    - https://gui.dandiarchive.org/#/dandiset/123456
    - DANDI:123456
    - DANDI Archive ID: 123456

    Parameters
    ----------
    articles : list[dict]
        List of article dictionaries, possibly with 'full_text' key.

    Returns
    -------
    list[dict]
        List of article dicts, each with a new key 'dandisets' (list of found Dandiset IDs/URLs).
    """
    dandiset_pattern = re.compile(
        r"(?:https?://)?(?:www\.|gui\.)?dandiarchive\.org/(?:dandiset/|#/?dandiset/)(\d{6})(?:/draft)?"
        r"|DANDI:?(\d{6})"
        r"|DANDI\s+Archive\s+ID:\s*(\d{6})"
        r"|(?:https?://doi\.org/)?10\.\d+/dandi\.(\d{6})/[\d\.]+|"
        r"dataset\s+number\s+(\d{6})|"
        r"DANDI\s+Archive.*?dataset\s+number\s+(\d{6})|"
        r"dandiarchive\.org.*?dataset\s+number\s+(\d{6})|"
        r"DANDI\s+archive\d*\.?\s*(\d{6})|"
        r"available\s+in\s+the\s+DANDI\s+archive\d*\.?\s*(\d{6})",
        re.IGNORECASE | re.DOTALL
    )
    for article in articles:
        dandisets = set()
        # Check full_text for Dandiset IDs
        full_text = article.get("full_text")
        if full_text is not None:
            for match in dandiset_pattern.finditer(full_text):
                ds_id = (match.group(1) or match.group(2) or match.group(3) or 
                        match.group(4) or match.group(5) or match.group(6) or 
                        match.group(7) or match.group(8) or match.group(9))
                if ds_id:
                    dandisets.add(ds_id)
        article["dandisets"] = sorted(dandisets)
    return articles

def has_full_text(article: dict) -> bool:
    """
    Check if the article has full text available.

    Some articles appear to have the full text but it's actually just the abstract and some metadata.
    To distinguish between the two, we use a character cutoff of 10,000. 

    Parameters
    ----------
    article : dict
        Article dictionary containing 'full_text' key.

    Returns
    -------
    bool
        True if full text is available, False otherwise.
    """
    full_text = article.get('full_text')
    if full_text is None or len(full_text) < 10000:
        return False
    return True

def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """
    Deduplicate articles based on title.

    Parameters
    ----------
    articles : list[dict]
        List of article dictionaries.

    Returns
    -------
    list[dict]
        List of deduplicated articles.
    """
    seen = set()
    deduped_articles = []
    
    for article in articles:
        title = article.get('title').lower()
        if title not in seen:
            seen.add(title)
            deduped_articles.append(article)

    return deduped_articles

# Example execution
if __name__ == "__main__":
    # Search for DANDI-related articles
    articles = search_dandi_articles(verbose=True)
    articles = extract_dandisets_from_articles(articles=articles)
    articles = deduplicate_articles(articles=articles)

    print(f"\nFound {len(articles)} articles likely referencing datasets:")

    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"PMID: {article['pmid']}")
        if article['doi']:
            print(f"DOI: {article['doi']}")
        if 'dandisets' in article:
            print(f"DANDI Sets: {', '.join(article['dandisets'])}")
        print(f"Has Full Text: {has_full_text(article)}")
