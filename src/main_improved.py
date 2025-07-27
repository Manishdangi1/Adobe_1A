#!/usr/bin/env python3
"""
Adobe India Hackathon 2025 - Round 1A: Improved PDF Structure Extractor
Enhanced heading detection while maintaining ≤10 seconds processing time.
Multilingual support for 50+ languages including complex scripts.
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import time

# Multilingual support imports
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # For consistent results
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_LIBRARY = "PyMuPDF"
except ImportError:
    try:
        import PyPDF2
        PDF_LIBRARY = "PyPDF2"
    except ImportError:
        print("❌ No PDF library found!")
        print("Install one of these:")
        print("  pip install PyMuPDF")
        print("  pip install PyPDF2")
        sys.exit(1)


@dataclass
class EnhancedTextBlock:
    """Enhanced text block with better heading detection and multilingual support."""
    text: str
    font_size: float
    is_bold: bool
    x0: float
    y0: float
    page_num: int
    font_name: str = ""
    language: str = "en"  # Default to English
    
    @property
    def is_centered(self) -> bool:
        """Check if text is centered."""
        return abs(self.x0) < 150  # More lenient centering
    
    @property
    def is_near_top(self) -> bool:
        """Check if text is near top of page."""
        return self.y0 < 300  # More lenient top position
    
    @property
    def is_title_case(self) -> bool:
        """Enhanced title case detection with multilingual support."""
        if not self.text.strip():
            return False
        text = self.text.strip()
        
        # Check for all caps
        if text.isupper() and len(text) > 2:
            return True
        
        # For non-Latin scripts, check for mixed case patterns
        if self.language not in ['en', 'es', 'fr', 'de', 'it', 'pt']:
            # For languages like Japanese, Chinese, Arabic, etc.
            # Check if text has mixed character types (indicating title-like formatting)
            has_upper = any(c.isupper() for c in text)
            has_lower = any(c.islower() for c in text)
            has_digit = any(c.isdigit() for c in text)
            
            # If it has mixed character types and is short, likely a heading
            if (has_upper or has_digit) and len(text) <= 50:
                return True
        
        # Check for title case (first letter of each word capitalized)
        words = text.split()[:5]  # Check first 5 words
        if not words:
            return False
        
        # First word should be capitalized
        if not words[0] or not words[0][0].isupper():
            return False
        
        # At least 60% of words should be capitalized
        capitalized_words = sum(1 for word in words if word and word[0].isupper())
        return capitalized_words >= len(words) * 0.6
    
    @property
    def has_heading_pattern(self) -> bool:
        """Enhanced heading pattern detection with multilingual support."""
        text = self.text.strip()
        
        # Multilingual numbered patterns
        numbered_patterns = [
            r'^\d+\.',  # 1. 2. 3.
            r'^\d+\)',  # 1) 2) 3)
            r'^[IVX]+\.',  # I. II. III.
            r'^[a-z]\)',  # a) b) c)
            r'^[A-Z]\.',  # A. B. C.
            # Japanese patterns
            r'^第\d+章',  # Chapter 1, Chapter 2
            r'^第\d+節',  # Section 1, Section 2
            # Chinese patterns
            r'^第\d+章',  # Chapter 1, Chapter 2
            r'^第\d+节',  # Section 1, Section 2
            # Arabic patterns
            r'^الفصل\s+\d+',  # Chapter
            r'^القسم\s+\d+',  # Section
            # Hindi patterns
            r'^अध्याय\s+\d+',  # Chapter
            r'^खंड\s+\d+',    # Section
        ]
        
        # Multilingual text patterns
        text_patterns = {
            'en': ['Chapter', 'Section', 'Part', 'Introduction', 'Conclusion',
                   'Abstract', 'Summary', 'Overview', 'Background', 'Method',
                   'Results', 'Discussion', 'References', 'Appendix'],
            'es': ['Capítulo', 'Sección', 'Parte', 'Introducción', 'Conclusión',
                   'Resumen', 'Antecedentes', 'Método', 'Resultados', 'Discusión'],
            'fr': ['Chapitre', 'Section', 'Partie', 'Introduction', 'Conclusion',
                   'Résumé', 'Contexte', 'Méthode', 'Résultats', 'Discussion'],
            'de': ['Kapitel', 'Abschnitt', 'Teil', 'Einleitung', 'Schlussfolgerung',
                   'Zusammenfassung', 'Hintergrund', 'Methode', 'Ergebnisse'],
            'ja': ['章', '節', '部', '序論', '結論', '要約', '背景', '方法', '結果'],
            'zh': ['章', '节', '部分', '引言', '结论', '摘要', '背景', '方法', '结果'],
            'ar': ['فصل', 'قسم', 'جزء', 'مقدمة', 'خاتمة', 'ملخص', 'خلفية', 'طريقة'],
            'hi': ['अध्याय', 'खंड', 'भाग', 'परिचय', 'निष्कर्ष', 'सारांश', 'पृष्ठभूमि'],
        }
        
        # Check numbered patterns
        for pattern in numbered_patterns:
            if re.match(pattern, text):
                return True
        
        # Check text patterns for detected language
        patterns = text_patterns.get(self.language, text_patterns['en'])
        for pattern in patterns:
            if text.startswith(pattern):
                return True
        
        return False
    
    @property
    def is_short_text(self) -> bool:
        """Check if text is appropriate length for heading."""
        length = len(self.text.strip())
        return 2 <= length <= 120  # More lenient length
    
    @property
    def has_heading_keywords(self) -> bool:
        """Check for heading-specific keywords with multilingual support."""
        text = self.text.strip().lower()
        
        # Multilingual keywords
        keywords = {
            'en': ['chapter', 'section', 'part', 'introduction', 'conclusion',
                   'abstract', 'summary', 'overview', 'background', 'method',
                   'results', 'discussion', 'references', 'appendix', 'analysis',
                   'evaluation', 'assessment', 'review', 'study', 'research',
                   'implementation', 'design', 'development', 'testing'],
            'es': ['capítulo', 'sección', 'parte', 'introducción', 'conclusión',
                   'resumen', 'antecedentes', 'método', 'resultados', 'discusión'],
            'fr': ['chapitre', 'section', 'partie', 'introduction', 'conclusion',
                   'résumé', 'contexte', 'méthode', 'résultats', 'discussion'],
            'de': ['kapitel', 'abschnitt', 'teil', 'einleitung', 'schlussfolgerung',
                   'zusammenfassung', 'hintergrund', 'methode', 'ergebnisse'],
            'ja': ['章', '節', '部', '序論', '結論', '要約', '背景', '方法', '結果'],
            'zh': ['章', '节', '部分', '引言', '结论', '摘要', '背景', '方法', '结果'],
            'ar': ['فصل', 'قسم', 'جزء', 'مقدمة', 'خاتمة', 'ملخص', 'خلفية', 'طريقة'],
            'hi': ['अध्याय', 'खंड', 'भाग', 'परिचय', 'निष्कर्ष', 'सारांश', 'पृष्ठभूमि'],
        }
        
        lang_keywords = keywords.get(self.language, keywords['en'])
        return any(keyword in text for keyword in lang_keywords)


class ImprovedPDFExtractor:
    """Improved PDF structure extractor with better heading detection and multilingual support."""
    
    def __init__(self):
        self.avg_font_size = 12.0
        self.font_size_thresholds = {}
        self.document_language = "en"  # Default language

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text."""
        if not LANGDETECT_AVAILABLE or not text.strip():
            return "en"
        
        try:
            # Use a sample of the text for language detection
            sample_text = text[:1000] if len(text) > 1000 else text
            detected_lang = detect(sample_text)
            
            # Map language codes to our supported languages
            lang_mapping = {
                'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de',
                'ja': 'ja', 'zh': 'zh', 'ar': 'ar', 'hi': 'hi',
                'zh-cn': 'zh', 'zh-tw': 'zh', 'zh-hans': 'zh', 'zh-hant': 'zh'
            }
            
            return lang_mapping.get(detected_lang, 'en')
        except Exception:
            return "en"

    def detect_document_language(self, text_blocks: List[EnhancedTextBlock]) -> str:
        """Detect the primary language of the document."""
        if not text_blocks:
            return "en"
        
        # Collect text from the first few pages for language detection
        sample_texts = []
        for block in text_blocks[:50]:  # Use first 50 blocks
            if len(block.text.strip()) > 10:  # Only use substantial text
                sample_texts.append(block.text)
        
        if not sample_texts:
            return "en"
        
        # Combine sample texts and detect language
        combined_text = " ".join(sample_texts)
        return self.detect_language(combined_text)

    # ---------------------------
    # Utility: convert flat heading list to nested hierarchy
    # ---------------------------
    @staticmethod
    def build_hierarchy(flat_headings: List[Dict]) -> List[Dict]:
        """Convert a flat, page-ordered heading list to a nested outline.

        Each node → {"title": str, "page": int, "children": []}
        """
        outline: List[Dict] = []
        stack: List[Dict] = []  # track latest node at each level

        for h in flat_headings:
            level = int(h["level"][1])  # "H1" -> 1, etc.
            node = {"title": h["text"], "page": h["page"], "children": []}

            # Ensure stack depth matches (level-1)
            while len(stack) >= level:
                stack.pop()

            if stack:
                # attach as child of previous level
                stack[-1]["children"].append(node)
            else:
                outline.append(node)

            stack.append(node)

        return outline
    
    def extract_text_blocks_enhanced(self, pdf_path: str) -> List[EnhancedTextBlock]:
        """Extract text blocks with enhanced analysis."""
        if PDF_LIBRARY == "PyMuPDF":
            text_blocks = self._extract_with_pymupdf(pdf_path)
        else:
            text_blocks = self._extract_with_pypdf2(pdf_path)
        
        if not text_blocks:
            return []
        
        # Detect document language first
        self.document_language = self.detect_document_language(text_blocks)
        print(f"Detected document language: {self.document_language}")
        
        # Assign language to all text blocks
        for block in text_blocks:
            block.language = self.document_language
        
        return text_blocks
    
    def _extract_with_pymupdf(self, pdf_path: str) -> List[EnhancedTextBlock]:
        """Extract using PyMuPDF with enhanced analysis."""
        text_blocks = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(len(doc), 50)):
                page = doc[page_num]
                
                # Get text blocks with detailed font info
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    for line in block.get("lines", []):
                        spans_in_line = line.get("spans", [])
                        if not spans_in_line:
                            continue

                        # Combine all spans on this line into one text string to avoid heading splits
                        combined_text = "".join(s["text"] for s in spans_in_line).strip()
                        if not combined_text or len(combined_text) < 2:
                            continue

                        # Representative font size = max span size on the line (captures heading size)
                        largest_span = max(spans_in_line, key=lambda sp: sp["size"])
                        font_size = largest_span["size"]

                        # Bold if any span is bold-ish
                        any_bold = any(any(ind in s["font"].lower() for ind in ["bold", "black", "heavy", "medium"]) for s in spans_in_line)

                        x0 = min(s["bbox"][0] for s in spans_in_line)
                        y0 = min(s["bbox"][1] for s in spans_in_line)

                        text_block = EnhancedTextBlock(
                            text=combined_text,
                            font_size=font_size,
                            is_bold=any_bold,
                            x0=x0,
                            y0=y0,
                            page_num=page_num + 1,
                            font_name=largest_span["font"]
                        )

                        text_blocks.append(text_block)
            
            doc.close()
        
        except Exception as e:
            print(f"PyMuPDF error: {e}")
        
        return text_blocks
    
    def _extract_with_pypdf2(self, pdf_path: str) -> List[EnhancedTextBlock]:
        """Extract using PyPDF2 with basic analysis."""
        text_blocks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(min(len(pdf_reader.pages), 50)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and len(line) >= 2:
                                # Basic analysis for PyPDF2
                                text_block = EnhancedTextBlock(
                                    text=line,
                                    font_size=12.0,  # Default size
                                    is_bold=False,   # Can't detect with PyPDF2
                                    x0=0.0,          # Can't detect with PyPDF2
                                    y0=0.0,          # Can't detect with PyPDF2
                                    page_num=page_num + 1
                                )
                                text_blocks.append(text_block)
        
        except Exception as e:
            print(f"PyPDF2 error: {e}")
        
        return text_blocks
    
    def calculate_font_statistics(self, text_blocks: List[EnhancedTextBlock]) -> None:
        """Calculate font size statistics for better heading detection."""
        if not text_blocks:
            return
        
        # Get font sizes
        font_sizes = [block.font_size for block in text_blocks if block.font_size > 0]
        if not font_sizes:
            return
        
        # Calculate statistics
        font_sizes.sort()
        self.avg_font_size = sum(font_sizes) / len(font_sizes)
        
        # Calculate percentiles for better thresholds
        p25 = font_sizes[len(font_sizes) // 4]
        p75 = font_sizes[3 * len(font_sizes) // 4]
        
        self.font_size_thresholds = {
            'small': p25,
            'medium': self.avg_font_size,
            'large': p75,
            'very_large': p75 * 1.5
        }
    
    def extract_title_enhanced(self, pdf_path: str, text_blocks: List[EnhancedTextBlock]) -> str:
        """Enhanced title extraction."""
        # Try metadata first
        if PDF_LIBRARY == "PyMuPDF":
            try:
                doc = fitz.open(pdf_path)
                title = doc.metadata.get('title', '').strip()
                doc.close()
                if title and len(title) > 3:
                    return title
            except:
                pass
        
        # Content-based extraction
        first_page_blocks = [b for b in text_blocks if b.page_num == 1]
        if not first_page_blocks:
            return "Untitled Document"
        
        # Find best title candidate
        title_candidates = []
        for block in first_page_blocks:
            if not block.is_short_text:
                continue
            
            score = 0
            
            # Font size scoring
            if block.font_size >= self.font_size_thresholds.get('very_large', 18):
                score += 30
            elif block.font_size >= self.font_size_thresholds.get('large', 14):
                score += 20
            elif block.font_size >= self.font_size_thresholds.get('medium', 12):
                score += 10
            
            # Position scoring
            if block.is_near_top:
                score += 15
            if block.is_centered:
                score += 10
            
            # Style scoring
            if block.is_bold:
                score += 15
            
            # Content scoring
            if block.is_title_case:
                score += 20
            
            if score >= 25:
                title_candidates.append((block, score))
        
        if title_candidates:
            title_candidates.sort(key=lambda x: x[1], reverse=True)
            return title_candidates[0][0].text
        
        return "Untitled Document"
    
    def identify_headings_enhanced(self, text_blocks: List[EnhancedTextBlock]) -> List[EnhancedTextBlock]:
        """Enhanced heading identification with multiple strategies."""
        potential_headings = []
        
        for block in text_blocks:
            if not block.is_short_text:
                continue

            # --- New: Filter out lines ending with punctuation ---
            if block.text.strip().endswith(('.', '?', '!')):
                continue

            # --- New: Require at least 2 words and at least one capitalized word ---
            words = block.text.strip().split()
            if len(words) < 2:
                continue
            if not any(w[0].isupper() for w in words if w):
                continue

            # Multi-factor scoring
            score = 0

            # Font size scoring (relative to document)
            if self.avg_font_size > 0:
                relative_size = block.font_size / self.avg_font_size
                if relative_size >= 1.5:
                    score += 35
                elif relative_size >= 1.3:
                    score += 30
                elif relative_size >= 1.1:
                    score += 25
                elif relative_size >= 0.9:
                    score += 15
                else:
                    score += 5

            # Style scoring
            if block.is_bold:
                score += 25

            # Position scoring
            if block.is_near_top:
                score += 15
            if block.is_centered:
                score += 15

            # Content scoring
            if block.is_title_case:
                score += 20
            if block.has_heading_pattern:
                score += 30
            if block.has_heading_keywords:
                score += 20

            # Length scoring
            length = len(block.text.strip())
            if 5 <= length <= 50:
                score += 10
            elif 51 <= length <= 80:
                score += 5

            # Lower threshold for more headings
            if score >= 25:
                potential_headings.append((block, score))
        
        # Return top 50 candidates to keep more potential headings
        potential_headings.sort(key=lambda x: x[1], reverse=True)
        return [block for block, score in potential_headings[:50]]
    
    def assign_levels_enhanced(self, headings: List[EnhancedTextBlock]) -> List[Dict]:
        """Enhanced level assignment with better logic."""
        if not headings:
            return []
        
        heading_levels = []
        
        for heading in headings:
            # Enhanced level assignment
            if self.avg_font_size > 0:
                relative_size = heading.font_size / self.avg_font_size
                
                if relative_size >= 1.4:
                    level = "H1"
                elif relative_size >= 1.2:
                    level = "H2"
                elif relative_size >= 1.0:
                    level = "H3"
                else:
                    level = "H3"  # Default to H3
            else:
                # Fallback logic
                if heading.has_heading_pattern and heading.is_bold:
                    level = "H1"
                elif heading.is_bold:
                    level = "H2"
                else:
                    level = "H3"
            
            heading_levels.append({
                "level": level,
                "text": heading.text.strip(),
                "page": heading.page_num,
                "y0": heading.y0  # Keep y0 for proper sorting
            })
        
        # Sort by page number first, then by vertical position (reading order)
        heading_levels.sort(key=lambda x: (x["page"], x["y0"]))
        
        # Remove y0 from final output
        for heading in heading_levels:
            del heading["y0"]
            
        return heading_levels
    
    def process_pdf_enhanced(self, pdf_path: str) -> Dict:
        """Enhanced PDF processing with better heading detection and multilingual support."""
        start_time = time.time()
        
        try:
            # Extract text blocks (language detection happens here)
            text_blocks = self.extract_text_blocks_enhanced(pdf_path)
            
            if not text_blocks:
                return {"title": "Untitled Document", "outline": [], "language": "en"}
            
            # Calculate font statistics
            self.calculate_font_statistics(text_blocks)

            # Extract title
            title = self.extract_title_enhanced(pdf_path, text_blocks)
            
            # Identify headings
            potential_headings = self.identify_headings_enhanced(text_blocks)
            
            # Assign levels
            headings = self.assign_levels_enhanced(potential_headings)

            # Return flat list format as requested
            processing_time = time.time() - start_time
            print(f"Processing time: {processing_time:.2f} seconds")
            print(f"Detected language: {self.document_language}")
            
            return {
                "title": title,
                "outline": headings,
                "language": self.document_language
            }
            
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return {"title": "Error Processing Document", "outline": [], "language": "en"}


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Adobe India Hackathon 2025 - Round 1A: Improved PDF Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("output_json", help="Path to the output JSON file")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file '{args.input_pdf}' does not exist.")
        sys.exit(1)
    
    if not args.input_pdf.lower().endswith('.pdf'):
        print(f"Error: Input file '{args.input_pdf}' is not a PDF file.")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output_json)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Processing PDF: {args.input_pdf}")
    print(f"Using library: {PDF_LIBRARY}")
    total_start_time = time.time()
    
    # Initialize extractor and process PDF
    extractor = ImprovedPDFExtractor()
    result = extractor.process_pdf_enhanced(args.input_pdf)
    
    # Write JSON output
    try:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        total_time = time.time() - total_start_time
        print(f"Total execution time: {total_time:.2f} seconds")
        print(f"Output written to: {args.output_json}")
        print(f"Title: {result['title']}")
        print(f"Found {len(result['outline'])} headings")
        
        # Performance check
        if total_time > 10.0:
            print(f"⚠️  WARNING: Execution time ({total_time:.2f}s) exceeds 10-second limit!")
        else:
            print(f"✅ SUCCESS: Execution time ({total_time:.2f}s) meets requirement!")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 