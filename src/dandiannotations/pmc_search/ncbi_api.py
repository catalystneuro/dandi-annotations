import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
import json
from typing import Literal
import re

class NcbiAPI:
    def __init__(self, email=None, api_key=None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = email  # Required for courtesy
        self.api_key = api_key  # Optional, increases rate limits

    def get_pmids(self, query: str, max_results: int = 100, database: Literal["pubmed", "pmc"] = "pubmed") -> list[str]:
        """
        Search with NCBI E-Utilities for articles matching query
        
        Parameters
        ----------
        query : str
            Search term to query NCBI databases
        max_results : int
            Maximum number of results to return (default 100)
        database : str
            Database to search in, either "pubmed" or "pmc" (default "pubmed")
        
        Returns
        -------
        list[str]
            List of PMIDs or PMCIDs matching the search query
        """
        url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': database,
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

    def get_article_details(self, pmids: list[str], database: Literal["pubmed", "pmc"] = "pubmed") -> list[dict]:
        """
        Get detailed information for list of PMIDs.

        Parameters
        ----------
        pmids : list[str]
            List of PMIDs or PMCIDs to retrieve details for
        database : str
            Database to fetch details from, either "pubmed" or "pmc" (default "pubmed")
        
        Returns
        -------
        list[dict]
            List of dictionaries containing article details
        """
        if isinstance(pmids, str):
            pmids = [pmids]
            
        url = f"{self.base_url}efetch.fcgi"
        params = {
            'db': database,
            'id': ','.join(pmids),
            'retmode': 'xml',
        }
        
        if self.email:
            params['email'] = self.email
        if self.api_key:
            params['api_key'] = self.api_key
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        if database == "pubmed":
            return self.parse_pubmed_xml(response.text)
        elif database == "pmc":
            return self.parse_pmc_xml(response.text)
        else:
            raise ValueError(f"Unsupported database: {database}")
        
    def parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        """
        Parse PubMed XML response into structured data.

        Parameters
        ----------
        xml_text : str
            Raw XML text from PubMed response

        Returns
        -------
        list[dict]
            List of dictionaries containing article details
        """
        root = ET.fromstring(xml_text)
        articles = []
        
        for article in root.findall('.//PubmedArticle'):
            article_data = {
                'pmid': self._extract_pubmed_pmid(article),
                'title': self._extract_pubmed_title(article),
                'abstract': self._extract_pubmed_abstract(article),
                'authors': self._extract_pubmed_authors(article),
                'journal': self._extract_pubmed_journal(article),
                'year': self._extract_pubmed_year(article),
                'doi': self._extract_pubmed_doi(article),
            }
            
            articles.append(article_data)
                
        return articles
    
    
    def parse_pmc_xml(self, xml_text: str) -> list[dict]:
        """
        Parse PMC XML response into structured data.

        Parameters
        ----------
        xml_text : str
            Raw XML text from PMC response

        Returns
        -------
        list[dict]
            List of dictionaries containing article details
        """
        root = ET.fromstring(xml_text)
        articles = []
        
        for article in root.findall('.//article'):
            article_data = {
                'pmc_id': self._extract_pmc_id(article),
                'pmid': self._extract_pmid(article),
                'title': self._extract_title(article),
                'doi': self._extract_doi(article),
                'full_text': self._extract_full_text(article),
            }
            
            articles.append(article_data)
                
        return articles

    def _extract_pubmed_pmid(self, article_elem: ET.Element) -> str:
        """
        Extract PMID from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        str
            PMID
        """
        pmid_elem = article_elem.find('.//PMID')
        return pmid_elem.text if pmid_elem is not None else None
    
    def _extract_pubmed_title(self, article_elem: ET.Element) -> str:
        """
        Extract article title from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        str
            Article title or "No title" if not found
        """
        title_elem = article_elem.find('.//ArticleTitle')
        return title_elem.text if title_elem is not None else "No title"
    
    def _extract_pubmed_doi(self, article_elem: ET.Element) -> str:
        """
        Extract DOI from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        str
            DOI or None if not found
        """
        doi_elem = article_elem.find('.//ArticleId[@IdType="doi"]')
        return doi_elem.text if doi_elem is not None else None
    
    def _extract_pmc_id(self, article_elem: ET.Element) -> str:
        """
        Extract PMC ID from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            PMC ID or None if not found
        """
        for article_id in article_elem.findall('.//article-id'):
            if article_id.get('pub-id-type') == 'pmc':
                return article_id.text
        return None
    
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
    api = NcbiAPI(email="paul.wesley.adkisson@gmail.com")
    
    # Search queries for DANDI-related articles
    database_to_queries = {
        # "pubmed": [
        #     '"DANDI Archive"[tiab:~0]',
        #     '"Distributed Archives for Neurophysiology Data Integration"[tiab:~0]'
        #     '"DANDI:"[tiab:~0]',
        # ],
        "pmc": [
            '"DANDI Archive"',
            # '"Distributed Archives for Neurophysiology Data Integration"',
        ]
    }
    all_articles = []

    for database, queries in database_to_queries.items():
        if verbose:
            print(f"Searching {database} for DANDI-related articles...")

        for query in queries:
            pmids = api.get_pmids(query, max_results=100, database=database)
            if verbose:
                print(f"Found {len(pmids)} articles for query: {query}")

            if pmids:
                articles = api.get_article_details(pmids, database=database)
                all_articles.extend(articles)
                if verbose:
                    print(f"Retrieved details for {len(articles)} articles.")
            else:
                if verbose:
                    print("No articles found for this query.")

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

# Example execution
if __name__ == "__main__":
    # Search for DANDI-related articles
    articles = search_dandi_articles(verbose=True)
    articles = extract_dandisets_from_articles(articles=articles)

    for article in articles:
        assert article["full_text"], f"Article {article['pmid']} has no full text available."

    print(f"\nFound {len(articles)} articles likely referencing datasets:")

    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"PMID: {article['pmid']}")
        if article['doi']:
            print(f"DOI: {article['doi']}")
        if 'dandisets' in article:
            print(f"DANDI Sets: {', '.join(article['dandisets'])}")
        print(f"Has Full Text: {has_full_text(article)}")
