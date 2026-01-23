"""
Document Loader for Inside the Paintbox
Extracts artwork information from HTML files
"""

from bs4 import BeautifulSoup
from pathlib import Path
import re


def clean_text(text):
    """Clean extracted text by removing extra whitespace"""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def load_artwork_from_html(html_path):
    """Extract artwork information from a single HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Extract title from h1
        title_elem = soup.find('h1')
        title = clean_text(title_elem.get_text()) if title_elem else ""

        # Extract subtitle/dimensions from h6
        subtitle_elem = soup.find('h6')
        subtitle = clean_text(subtitle_elem.get_text()) if subtitle_elem else ""

        # Extract description from paragraphs
        paragraphs = soup.find_all('p')
        description = " ".join([clean_text(p.get_text()) for p in paragraphs])

        # Extract any h2 headers (like "INSPIRATION")
        headers = soup.find_all('h2')
        section_titles = " ".join([clean_text(h.get_text()) for h in headers])

        # Combine all content
        full_content = f"""
Artwork: {title}
{subtitle}

{description}
        """.strip()

        return {
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "content": full_content,
            "source": str(html_path)
        }
    except Exception as e:
        print(f"Error loading {html_path}: {e}")
        return None


def load_all_artworks(website_path):
    """Load all artwork documents from the website"""
    documents = []
    website_path = Path(website_path)

    # Look for artwork HTML files in multiple locations
    artwork_paths = [
        website_path / "artworks",
        website_path / "pages" / "artworks",
    ]

    for artwork_dir in artwork_paths:
        if artwork_dir.exists():
            for html_file in artwork_dir.glob("*.html"):
                doc = load_artwork_from_html(html_file)
                if doc and doc["content"]:
                    documents.append(doc)
                    print(f"Loaded: {doc['title']}")

    # Also load series pages for additional context
    series_path = website_path / "pages" / "series"
    if series_path.exists():
        for html_file in series_path.glob("*.html"):
            doc = load_artwork_from_html(html_file)
            if doc and doc["content"]:
                documents.append(doc)
                print(f"Loaded series: {doc['title']}")

    return documents


def load_about_page(website_path):
    """Load the about page for artist information"""
    about_path = Path(website_path) / "pages" / "about.html"
    if about_path.exists():
        doc = load_artwork_from_html(about_path)
        if doc:
            doc["title"] = "About the Artist"
            return doc
    return None


if __name__ == "__main__":
    # Test the loader
    docs = load_all_artworks("../")
    print(f"\nLoaded {len(docs)} documents")
    for doc in docs[:3]:
        print(f"\n--- {doc['title']} ---")
        print(doc['content'][:200] + "...")
