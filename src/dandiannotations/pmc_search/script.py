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
            'rettype': 'full',
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
                
                # Also extract from floats-group (figures, tables, etc.)
                floats_content = {
                    'figures': [],
                    'tables': [],
                    'boxed_text': [],
                    'supplementary': []
                }
                
                floats_group = article.find('.//floats-group')
                
                # Extract figures
                for fig in floats_group.findall('.//fig'):
                    figure_data = {
                        'id': fig.get('id'),
                        'label': '',
                        'title': '',
                        'caption': '',
                        'graphic_href': ''
                    }
                    
                    # Figure label
                    label_elem = fig.find('.//label')
                    if label_elem is not None:
                        figure_data['label'] = label_elem.text
                    
                    # Figure title and caption
                    caption_elem = fig.find('.//caption')
                    if caption_elem is not None:
                        title_elem = caption_elem.find('.//title')
                        if title_elem is not None:
                            figure_data['title'] = title_elem.text

                        # Extract all caption paragraphs
                        caption_parts = []
                        for p in caption_elem.findall('.//p'):
                            caption_parts.append(p.text)
                        figure_data['caption'] = ' '.join(caption_parts)
                    
                    # Graphic file reference
                    graphic_elem = fig.find('.//graphic')
                    if graphic_elem is not None:
                        href = graphic_elem.get('{http://www.w3.org/1999/xlink}href')
                        if href:
                            figure_data['graphic_href'] = href
                    
                    floats_content['figures'].append(figure_data)
                
                # Extract tables
                for table_wrap in floats_group.findall('.//table-wrap'):
                    table_data = {
                        'id': table_wrap.get('id'),
                        'label': '',
                        'caption': '',
                        'headers': [],
                        'rows': []
                    }
                    
                    # Table label
                    label_elem = table_wrap.find('.//label')
                    if label_elem is not None:
                        table_data['label'] = label_elem.text

                    # Table caption
                    caption_elem = table_wrap.find('.//caption')
                    if caption_elem is not None:
                        table_data['caption'] = caption_elem.text

                    # Extract table headers
                    table_elem = table_wrap.find('.//table')
                    if table_elem is not None:
                        # Headers
                        for th in table_elem.findall('.//thead//th'):
                            header_text = th.text
                            if header_text is not None:
                                table_data['headers'].append(header_text)
                        
                        # Table rows
                        for tr in table_elem.findall('.//tbody//tr'):
                            row_data = []
                            for td in tr.findall('.//td'):
                                cell_text = td.text
                                if cell_text is not None:
                                    row_data.append(cell_text.strip())
                            if any(cell.strip() for cell in row_data):  # Skip empty rows
                                table_data['rows'].append(row_data)
                    
                    floats_content['tables'].append(table_data)
                
                # Extract boxed text (highlights, key points, etc.)
                for boxed in floats_group.findall('.//boxed-text'):
                    boxed_data = {
                        'id': boxed.get('id'),
                        'title': '',
                        'content': []
                    }
                    
                    # Boxed text title
                    caption_elem = boxed.find('.//caption')
                    if caption_elem is not None:
                        title_elem = caption_elem.find('.//title')
                        if title_elem is not None:
                            boxed_data['title'] = title_elem.text

                    # Extract list items or paragraphs
                    for list_item in boxed.findall('.//list-item'):
                        item_text = list_item.text
                        if item_text is not None:
                            boxed_data['content'].append(item_text)
                    
                    # If no list items, try paragraphs
                    if not boxed_data['content']:
                        for p in boxed.findall('.//p'):
                            para_text = p.text
                            if para_text is not None:
                                boxed_data['content'].append(para_text)
                    
                    floats_content['boxed_text'].append(boxed_data)
                
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
                    'references': references,
                    'figures': floats_content['figures'],
                    'tables': floats_content['tables'],
                    'boxed_text': floats_content['boxed_text'],
                    'supplementary': floats_content['supplementary'],
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
        print(f"Searching {database} for DANDI-related articles...")

        for query in queries:
            pmids = api.search(query, max_results=100, database=database)
            pmids = ['11265976']
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
        r"|DANDI\s+Archive\s+ID:\s*(\d{6})",
        re.IGNORECASE
    )
    for article in articles:
        dandisets = set()
        # Check full_text for Dandiset IDs
        full_text = article.get("full_text")
        if full_text is not None:
            for match in dandiset_pattern.finditer(full_text):
                ds_id = match.group(1) or match.group(2) or match.group(3)
                if ds_id:
                    dandisets.add(ds_id)
        # Check tables for Dandiset IDs
        for table in article.get("tables", []):
            # Check rows
            for row in table.get("rows", []):
                for cell in row:
                    if cell:
                        for match in dandiset_pattern.finditer(cell):
                            ds_id = match.group(1) or match.group(2) or match.group(3)
                            if ds_id:
                                dandisets.add(ds_id)
        article["dandisets"] = sorted(dandisets)
    return articles

# Example execution
if __name__ == "__main__":
    # Search for DANDI-related articles
    articles = search_dandi_articles()
    articles = extract_dandisets_from_articles(articles=articles)

    print(f"\nFound {len(articles)} articles likely referencing datasets:")

    for article in articles[:10]:  # Show first 5
        print(f"\nTitle: {article['title']}")
        print(f"Authors: {', '.join(article['authors'][:3])}{'...' if len(article['authors']) > 3 else ''}")
        print(f"Journal: {article['journal']} ({article['year']})")
        print(f"PMID: {article['pmid']}")
        if article['doi']:
            print(f"DOI: {article['doi']}")
        if 'dandisets' in article:
            print(f"DANDI Sets: {', '.join(article['dandisets'])}")
        if 'full_text' in article:
            print(f"Full Text: {article['full_text'][-50:]}")
        print(article["tables"])