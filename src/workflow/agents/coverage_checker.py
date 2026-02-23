from typing import List, Set, Dict
from src.models.context import DocumentContext
from src.models.slide import SlideContent
import re

class ContentCoverageChecker:
    def extract_key_phrases(self, text: str) -> Set[str]:
        text_lower = text.lower()
        
        sentences = re.split(r'[.!?\n]+', text_lower)
        phrases = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            words = sentence.split()
            if len(words) >= 3:
                phrases.add(' '.join(words[:10]))
        
        return phrases
    
    def check_coverage(
        self, 
        source_text: str, 
        slides: List[SlideContent]
    ) -> Dict[str, any]:
        source_phrases = self.extract_key_phrases(source_text)
        
        all_slide_text = ""
        for slide in slides:
            all_slide_text += " " + slide.slide_title
            all_slide_text += " " + " ".join(slide.content)
        
        slide_phrases = self.extract_key_phrases(all_slide_text)
        
        covered = 0
        for source_phrase in source_phrases:
            for slide_phrase in slide_phrases:
                if source_phrase in slide_phrase or slide_phrase in source_phrase:
                    covered += 1
                    break
        
        coverage_percent = (covered / len(source_phrases)) * 100 if source_phrases else 100
        
        missing_content = []
        source_sentences = re.split(r'[.!?\n]+', source_text)
        for sent in source_sentences:
            sent = sent.strip()
            if len(sent) < 20:
                continue
            
            found = False
            for slide_phrase in slide_phrases:
                if sent.lower()[:30] in slide_phrase or slide_phrase in sent.lower()[:30]:
                    found = True
                    break
            
            if not found:
                missing_content.append(sent[:100])
        
        return {
            "coverage_percent": round(coverage_percent, 2),
            "missing_count": len(missing_content),
            "missing_content": missing_content[:5]
        }

