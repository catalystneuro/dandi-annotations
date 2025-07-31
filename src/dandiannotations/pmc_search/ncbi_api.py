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
                'abstract': self._extract_abstract(article),
                'authors': self._extract_authors(article),
                'journal': self._extract_journal(article),
                'year': self._extract_year(article),
                'doi': self._extract_doi(article),
                'full_text': self._extract_full_text(article),
                'references': self._extract_references(article),
                'figures': self._extract_figures(article),
                'tables': self._extract_tables(article),
                'boxed_text': self._extract_boxed_text(article),
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
    
    def _extract_pubmed_abstract(self, article_elem: ET.Element) -> str:
        """
        Extract abstract from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        str
            Abstract text or "No abstract" if not found
        """
        abstract_elem = article_elem.find('.//AbstractText')
        return abstract_elem.text if abstract_elem is not None else "No abstract"
    
    def _extract_pubmed_authors(self, article_elem: ET.Element) -> list[str]:
        """
        Extract authors from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        list[str]
            List of author names
        """
        authors = []
        for author in article_elem.findall('.//Author'):
            lastname = author.find('LastName')
            forename = author.find('ForeName')
            if lastname is not None and forename is not None:
                authors.append(f"{forename.text} {lastname.text}")
        return authors
    
    def _extract_pubmed_journal(self, article_elem: ET.Element) -> str:
        """
        Extract journal name from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        str
            Journal name or "Unknown journal" if not found
        """
        journal_elem = article_elem.find('.//Journal/Title')
        return journal_elem.text if journal_elem is not None else "Unknown journal"
    
    def _extract_pubmed_year(self, article_elem: ET.Element) -> str:
        """
        Extract publication year from PubMed article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The PubMed article XML element
            
        Returns
        -------
        str
            Publication year or "Unknown year" if not found
        """
        pub_date = article_elem.find('.//PubDate/Year')
        return pub_date.text if pub_date is not None else "Unknown year"
    
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
            if article_id.get('pub-id-type') == 'pmid':
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
    
    def _extract_abstract(self, article_elem: ET.Element) -> str:
        """
        Extract abstract from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            Abstract text or "No abstract" if not found
        """
        abstract_parts = []
        for abstract in article_elem.findall('.//abstract//p'):
            if abstract.text:
                abstract_parts.append(abstract.text)
        return ' '.join(abstract_parts) if abstract_parts else "No abstract"
    
    def _extract_authors(self, article_elem: ET.Element) -> list[str]:
        """
        Extract authors from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        list[str]
            List of author names
        """
        authors = []
        for contrib in article_elem.findall('.//contrib[@contrib-type="author"]'):
            given_names = contrib.find('.//given-names')
            surname = contrib.find('.//surname')
            if given_names is not None and surname is not None:
                authors.append(f"{given_names.text} {surname.text}")
        return authors
    
    def _extract_journal(self, article_elem: ET.Element) -> str:
        """
        Extract journal name from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            Journal name or "Unknown journal" if not found
        """
        journal_elem = article_elem.find('.//journal-title')
        return journal_elem.text if journal_elem is not None else "Unknown journal"
    
    def _extract_year(self, article_elem: ET.Element) -> str:
        """
        Extract publication year from article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            Publication year or "Unknown year" if not found
        """
        pub_date = article_elem.find('.//pub-date[@pub-type="epub"]//year')
        if pub_date is None:
            pub_date = article_elem.find('.//pub-date//year')
        return pub_date.text if pub_date is not None else "Unknown year"
    
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
        Extract full text content from the article body.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        str
            The full text content of the article
        """
        body_elem = article_elem.find('.//body')
        if body_elem is not None:
            return ''.join(body_elem.itertext()).strip()
        return ""
    
    def _extract_references(self, article_elem: ET.Element) -> list[str]:
        """
        Extract references from the article.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        list[str]
            List of reference strings
        """
        references = []
        for ref in article_elem.findall('.//ref'):
            ref_text = ET.tostring(ref, encoding='unicode', method='text')
            references.append(ref_text.strip())
        return references
    
    def _extract_figures(self, article_elem: ET.Element) -> list[dict]:
        """
        Extract figure data from the article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        list[dict]
            List of figure dictionaries with metadata
        """
        figures = []
        
        floats_group_elem = article_elem.find('.//floats-group')
        if floats_group_elem is None:
            return figures
            
        for fig in floats_group_elem.findall('.//fig'):
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
                    if p.text:
                        caption_parts.append(p.text)
                figure_data['caption'] = ' '.join(caption_parts)
            
            # Graphic file reference
            graphic_elem = fig.find('.//graphic')
            if graphic_elem is not None:
                href = graphic_elem.get('{http://www.w3.org/1999/xlink}href')
                if href:
                    figure_data['graphic_href'] = href
            
            figures.append(figure_data)
        
        return figures
    
    def _extract_tables(self, article_elem: ET.Element) -> list[dict]:
        """
        Extract table data from the article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        list[dict]
            List of table dictionaries with metadata and content
        """
        tables = []
        
        floats_group_elem = article_elem.find('.//floats-group')
        if floats_group_elem is None:
            return tables
            
        for table_wrap in floats_group_elem.findall('.//table-wrap'):
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

            # Extract table headers and rows
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
            
            tables.append(table_data)
        
        return tables
    
    def _extract_boxed_text(self, article_elem: ET.Element) -> list[dict]:
        """
        Extract boxed text content from the article element.
        
        Parameters
        ----------
        article_elem : ET.Element
            The article XML element
            
        Returns
        -------
        list[dict]
            List of boxed text dictionaries with content
        """
        boxed_texts = []
        
        floats_group_elem = article_elem.find('.//floats-group')
        if floats_group_elem is None:
            return boxed_texts
            
        for boxed in floats_group_elem.findall('.//boxed-text'):
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
            
            boxed_texts.append(boxed_data)
        
        return boxed_texts

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
            '"Distributed Archives for Neurophysiology Data Integration"',
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
        # Check tables for Dandiset IDs
        for table in article.get("tables", []):
            # Check rows
            for row in table.get("rows", []):
                for cell in row:
                    if cell:
                        for match in dandiset_pattern.finditer(cell):
                            ds_id = (match.group(1) or match.group(2) or match.group(3) or 
                                    match.group(4) or match.group(5) or match.group(6) or 
                                    match.group(7) or match.group(8) or match.group(9))
                            if ds_id:
                                dandisets.add(ds_id)
        article["dandisets"] = sorted(dandisets)
    return articles

# Example execution
if __name__ == "__main__":
    # Search for DANDI-related articles
    articles = search_dandi_articles(verbose=True)
    articles = extract_dandisets_from_articles(articles=articles)

    for article in articles:
        assert article["full_text"], f"Article {article['pmid']} has no full text available."

    print(f"\nFound {len(articles)} articles likely referencing datasets:")

    for article in articles[:5]:  # Show first 5
        print(f"\nTitle: {article['title']}")
        print(f"Authors: {', '.join(article['authors'][:3])}{'...' if len(article['authors']) > 3 else ''}")
        print(f"Journal: {article['journal']} ({article['year']})")
        print(f"PMID: {article['pmid']}")
        if article['doi']:
            print(f"DOI: {article['doi']}")
        if 'dandisets' in article:
            print(f"DANDI Sets: {', '.join(article['dandisets'])}")
