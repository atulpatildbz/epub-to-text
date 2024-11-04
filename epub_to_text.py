import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import os
import argparse
import sys

def epub_to_text(epub_path, output_path):
    """
    Convert EPUB file to text while preserving chapter structure.
    
    Args:
        epub_path (str): Path to the EPUB file
        output_path (str): Path where the text file will be saved
    """
    # Verify input file exists
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
        
    # Read EPUB file
    book = epub.read_epub(epub_path)
    
    # Get the title of the book
    book_title = book.get_metadata('DC', 'title')[0][0]
    
    # Initialize variables
    chapter_number = 1
    full_text = []
    
    # Add book title at the start
    full_text.append(f"# {book_title}\n\n")
    
    def clean_html_content(html_content):
        """Clean HTML content and extract text."""
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text

    # Process each document in the EPUB
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Get content
            content = item.get_content().decode('utf-8')
            
            # Check if this looks like a chapter
            is_chapter = bool(re.search(r'chapter|prologue|epilogue', content.lower()))
            
            # Clean the content
            text = clean_html_content(content)
            
            # Skip if the content is too short (likely navigation or other metadata)
            if len(text.strip()) < 100:
                continue
                
            # Try to extract chapter title
            chapter_title = None
            soup = BeautifulSoup(content, 'html.parser')
            headers = soup.find_all(['h1', 'h2', 'h3'])
            
            for header in headers:
                header_text = header.get_text().strip()
                if header_text and len(header_text) < 100:  # Reasonable chapter title length
                    chapter_title = header_text
                    break
            
            # Add chapter marker
            if is_chapter:
                if chapter_title:
                    full_text.append(f"\n\n# Chapter {chapter_number}: {chapter_title}\n\n")
                else:
                    full_text.append(f"\n\n# Chapter {chapter_number}\n\n")
                chapter_number += 1
            
            # Add the cleaned text
            full_text.append(text)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(full_text))
    
    return f"Successfully converted '{book_title}' to text format at {output_path}"

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Convert EPUB files to text while preserving chapter structure.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add arguments
    parser.add_argument(
        'input',
        help='Path to the input EPUB file'
    )
    parser.add_argument(
        'output',
        help='Path where the output text file will be saved'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Convert the file
        result = epub_to_text(args.input, args.output)
        print(result)
        
        if args.verbose:
            print(f"\nInput file: {args.input}")
            print(f"Output file: {args.output}")
            print(f"File size: {os.path.getsize(args.output)} bytes")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
