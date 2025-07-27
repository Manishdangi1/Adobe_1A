#!/usr/bin/env python3
"""
Adobe India Hackathon 2025 - Challenge 1a: PDF Processing Solution
Main processing script that handles all PDFs in the input directory.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List

# Import our PDF extractor
from src.main_improved import ImprovedPDFExtractor


def process_pdfs():
    """
    Main function to process all PDFs in the input directory.
    Reads from /app/input and writes to /app/output.
    """
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the PDF extractor
    extractor = ImprovedPDFExtractor()
    
    # Get all PDF files from input directory
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in input directory")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    total_start_time = time.time()
    
    # Process each PDF file
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        
        try:
            # Generate output filename
            output_file = output_dir / f"{pdf_file.stem}.json"
            
            # Process the PDF
            start_time = time.time()
            result = extractor.process_pdf_enhanced(str(pdf_file))
            processing_time = time.time() - start_time
            
            # Write JSON output
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully processed {pdf_file.name}")
            print(f"   - Title: {result['title']}")
            print(f"   - Headings found: {len(result['outline'])}")
            print(f"   - Processing time: {processing_time:.2f}s")
            print(f"   - Output: {output_file.name}")
            
            # Performance check
            if processing_time > 10.0:
                print(f"   ⚠️  WARNING: Processing time ({processing_time:.2f}s) exceeds 10-second limit!")
            else:
                print(f"   ✅ Processing time ({processing_time:.2f}s) meets requirement!")
                
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")
            # Create error output with empty structure
            error_result = {
                "title": f"Error processing {pdf_file.name}",
                "outline": []
            }
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)
    
    total_time = time.time() - total_start_time
    print(f"\n🎉 Processing complete!")
    print(f"   - Total files processed: {len(pdf_files)}")
    print(f"   - Total execution time: {total_time:.2f}s")
    print(f"   - Output directory: {output_dir}")


def main():
    """Entry point for the application."""
    print("Adobe India Hackathon 2025 - Challenge 1a: PDF Processing Solution")
    print("=" * 70)
    
    # Check if running in Docker environment
    input_dir = Path("/app/input")
    if not input_dir.exists():
        print("Error: Input directory /app/input not found!")
        print("Make sure you're running this in the Docker container with proper volume mounts.")
        sys.exit(1)
    
    # Process all PDFs
    process_pdfs()


if __name__ == "__main__":
    main() 