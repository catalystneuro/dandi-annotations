import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time
import json
from typing import Literal

class NcbiAPI:
    def __init__(self, email=None, api_key=None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = email  # Required for courtesy
        self.api_key = api_key  # Optional, increases rate limits

    def search(self, query: str, max_results: int = 100, database: Literal["pubmed", "pmc"] = "pubmed") -> list[str]:
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
            'rettype': 'abstract'
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
        Parse PubMed XML response into structured data

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
            try:
                # Basic info
                pmid = article.find('.//PMID').text
                title_elem = article.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else "No title"
                
                # Abstract
                abstract_elem = article.find('.//AbstractText')
                abstract = abstract_elem.text if abstract_elem is not None else "No abstract"
                
                # Authors
                authors = []
                for author in article.findall('.//Author'):
                    lastname = author.find('LastName')
                    forename = author.find('ForeName')
                    if lastname is not None and forename is not None:
                        authors.append(f"{forename.text} {lastname.text}")
                
                # Journal info
                journal_elem = article.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                
                # Publication date
                pub_date = article.find('.//PubDate/Year')
                year = pub_date.text if pub_date is not None else "Unknown year"
                
                # DOI
                doi_elem = article.find('.//ArticleId[@IdType="doi"]')
                doi = doi_elem.text if doi_elem is not None else None
                
                articles.append({
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'doi': doi
                })
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
                
        return articles
    
    def parse_pmc_xml(self, xml_text):
        """
        Parse PMC XML response into structured data

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
            try:
                # PMC ID
                pmc_id = None
                for article_id in article.findall('.//article-id'):
                    if article_id.get('pub-id-type') == 'pmc':
                        pmc_id = article_id.text
                        break
                
                # Title
                title_elem = article.find('.//article-title')
                title = title_elem.text if title_elem is not None else "No title"
                
                # Abstract - PMC structure is different
                abstract_parts = []
                for abstract in article.findall('.//abstract//p'):
                    if abstract.text:
                        abstract_parts.append(abstract.text)
                abstract = ' '.join(abstract_parts) if abstract_parts else "No abstract"
                
                # Authors
                authors = []
                for contrib in article.findall('.//contrib[@contrib-type="author"]'):
                    given_names = contrib.find('.//given-names')
                    surname = contrib.find('.//surname')
                    if given_names is not None and surname is not None:
                        authors.append(f"{given_names.text} {surname.text}")
                
                # Journal info
                journal_elem = article.find('.//journal-title')
                journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                
                # Publication date
                pub_date = article.find('.//pub-date[@pub-type="epub"]//year')
                if pub_date is None:
                    pub_date = article.find('.//pub-date//year')
                year = pub_date.text if pub_date is not None else "Unknown year"
                
                # DOI
                doi_elem = None
                for article_id in article.findall('.//article-id'):
                    if article_id.get('pub-id-type') == 'doi':
                        doi_elem = article_id
                        break
                doi = doi_elem.text if doi_elem is not None else None
                
                # PMID (cross-reference)
                pmid = None
                for article_id in article.findall('.//article-id'):
                    if article_id.get('pub-id-type') == 'pmid':
                        pmid = article_id.text
                        break
                
                # Full text content - extract main body
                body_text = []
                for p in article.findall('.//body//p'):
                    if p.text:
                        body_text.append(p.text)
                full_text = ' '.join(body_text) if body_text else ""
                
                # References
                references = []
                for ref in article.findall('.//ref'):
                    ref_text = ET.tostring(ref, encoding='unicode', method='text')
                    references.append(ref_text.strip())
                
                articles.append({
                    'pmc_id': pmc_id,
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'full_text': full_text,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'doi': doi,
                    'references': references
                })
                
            except Exception as e:
                print(f"Error parsing PMC article: {e}")
                continue
                
        return articles

# Example usage for DANDI research
def search_dandi_articles():
    # Initialize API (replace with your email)
    api = NcbiAPI(email="paul.wesley.adkisson@gmail.com")
    
    # Search queries for DANDI-related articles
    database_to_queries = {
        "pubmed": [
            '"DANDI Archive"[tiab:~0]',
            '"Distributed Archives for Neurophysiology Data Integration"[tiab:~0]'
            '"DANDI:"[tiab:~0]',
        ],
        "pmc": [
            '"DANDI Archive"',
            '"Distributed Archives for Neurophysiology Data Integration"',
        ]
    }
    all_articles = []

    for database, queries in database_to_queries.items():
        print(f"Searching {database} for DANDI-related articles...")

        for query in queries:
            pmids = api.search(query, max_results=100, database=database)
            print(f"Found {len(pmids)} articles for query: {query}")

            if pmids:
                articles = api.get_article_details(pmids, database=database)
                all_articles.extend(articles)
                print(f"Retrieved details for {len(articles)} articles.")
            else:
                print("No articles found for this query.")
        
            # Rate limiting - be nice to NCBI servers
            time.sleep(1)
    
    return all_articles

# Example execution
if __name__ == "__main__":
    # Search for DANDI-related articles
    articles = search_dandi_articles()

    print(f"\nFound {len(articles)} articles likely referencing datasets:")

    for article in articles[:10]:  # Show first 5
        print(f"\nTitle: {article['title']}")
        print(f"Authors: {', '.join(article['authors'][:3])}{'...' if len(article['authors']) > 3 else ''}")
        print(f"Journal: {article['journal']} ({article['year']})")
        print(f"PMID: {article['pmid']}")
        if article['doi']:
            print(f"DOI: {article['doi']}")