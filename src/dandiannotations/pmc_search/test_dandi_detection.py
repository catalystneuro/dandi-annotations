#!/usr/bin/env python3
"""
Simple test script to check DANDI set detection in articles.
Run this script to see which articles need manual review for DANDI set association.
"""

from ncbi_api import search_dandi_articles, extract_dandisets_from_articles, has_full_text


def find_dandi_context_windows(text, window_size=50):
    """Find all occurrences of 'DANDI' and return context windows around them."""
    if not text:
        return []
    
    import re
    contexts = []
    text_lower = text.lower()
    
    # Find all positions where 'dandi' appears
    start = 0
    while True:
        pos = text_lower.find('dandi', start)
        if pos == -1:
            break
            
        # Extract context window
        start_pos = max(0, pos - window_size)
        end_pos = min(len(text), pos + 5 + window_size)  # 5 is length of 'dandi'
        
        context = text[start_pos:end_pos]
        # Clean up the context (remove excessive whitespace)
        context = ' '.join(context.split())
        
        # Mark the DANDI occurrence
        dandi_start = pos - start_pos
        if start_pos > 0:
            context = "..." + context
            dandi_start += 3
        if end_pos < len(text):
            context = context + "..."
            
        contexts.append({
            'context': context,
            'position': pos,
            'dandi_start': dandi_start
        })
        
        start = pos + 1
    
    return contexts


def test_article_dandi_detection():
    """Run DANDI detection on articles and print results with DOIs for easy searching."""
    
    print("Searching for DANDI-related articles...")
    articles = search_dandi_articles()
    
    print("Extracting DANDI sets from articles...")
    articles_with_dandi = extract_dandisets_from_articles(articles)
    
    # Separate articles with and without DANDI sets
    with_dandi = [a for a in articles_with_dandi if a['dandisets']]
    without_dandi = [a for a in articles_with_dandi if not a['dandisets']]
    
    # Summary stats
    print(f"\n{'='*60}")
    print(f"DANDI DETECTION RESULTS")
    print(f"{'='*60}")
    print(f"Total articles found: {len(articles_with_dandi)}")
    print(f"Articles with DANDI sets detected: {len(with_dandi)}")
    print(f"Articles WITHOUT DANDI sets: {len(without_dandi)}")
    
    # Articles needing review (no DANDI sets found)
    if without_dandi:
        print(f"\n{'='*60}")
        print(f"ARTICLES NEEDING REVIEW ({len(without_dandi)})")
        print(f"{'='*60}")
        
        for i, article in enumerate(without_dandi):
            doi = article.get('doi', 'No DOI available')
            title = article.get('title', 'No title')
            
            print(f"\n{i+1}. {title}")
            print(f"   DOI: {doi}")
            print(f"   PMID: {article.get('pmid', 'No PMID')}")
            print(f"   {'-'*50}")

            full_text = article.get('full_text', '')
            contexts = find_dandi_context_windows(full_text)
                
            # Show full text contexts
            for i, ctx in enumerate(contexts):
                print(f"  {i+1}. \"{ctx['context']}\"")

            if not contexts:
                assert not has_full_text(article), f"Article {doi} has no DANDI mentions but has full text (> 10,000 characters)."
                print(f"Article {doi} has no DANDI mentions and no full text available.")


if __name__ == "__main__":
    test_article_dandi_detection()
