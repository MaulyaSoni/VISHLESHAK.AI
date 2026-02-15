"""
Response Formatter for FINBOT v4
Formats responses professionally with consistent structure
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Format responses for professional, consistent output
    
    Features:
    - Consistent structure
    - Professional tone
    - Proper formatting
    - Section organization
    - Visual elements (emojis, separators)
    
    Usage:
        formatter = ResponseFormatter()
        formatted = formatter.format_response(raw_response, context)
    """
    
    def __init__(self):
        """Initialize response formatter"""
        self.section_icons = {
            "summary": "📊",
            "analysis": "🔍",
            "insights": "💡",
            "recommendations": "🎯",
            "data": "📈",
            "warning": "⚠️",
            "success": "✅",
            "error": "❌",
            "info": "ℹ️",
            "question": "❓",
            "answer": "💬",
            "steps": "🔢",
            "conclusion": "🏁"
        }
        
        logger.info("✅ Response formatter initialized")
    
    def format_response(
        self,
        response: str,
        context: Optional[Dict] = None,
        response_type: str = "standard",
        quality_score: Optional[float] = None
    ) -> str:
        """
        Format response professionally
        
        Args:
            response: Raw response text
            context: Context information
            response_type: Type of response (standard, analytical, conversational)
            quality_score: Optional quality score to display
            
        Returns:
            Formatted response
        """
        # Clean response
        response = self._clean_response(response)
        
        # Detect structure
        has_sections = self._has_sections(response)
        
        if response_type == "analytical":
            formatted = self._format_analytical(response, quality_score)
        elif response_type == "conversational":
            formatted = self._format_conversational(response)
        else:
            if has_sections:
                formatted = self._format_structured(response, quality_score)
            else:
                formatted = self._format_simple(response, quality_score)
        
        return formatted
    
    def _clean_response(self, response: str) -> str:
        """Clean up response text"""
        # Remove excessive newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        # Remove trailing whitespace
        response = response.strip()
        
        # Fix spacing around punctuation
        response = re.sub(r'\s+([.,!?])', r'\1', response)
        
        return response
    
    def _has_sections(self, response: str) -> bool:
        """Check if response has sections"""
        # Look for section headers
        section_patterns = [
            r'^#{1,3}\s+\w+',  # Markdown headers
            r'^\*\*[A-Z][^*]+\*\*:',  # Bold headers
            r'^[A-Z][A-Z\s]+:',  # ALL CAPS headers
        ]
        
        for pattern in section_patterns:
            if re.search(pattern, response, re.MULTILINE):
                return True
        
        return False
    
    def _format_simple(self, response: str, quality_score: Optional[float]) -> str:
        """Format simple response"""
        formatted_parts = []
        
        # Add quality indicator if available
        if quality_score is not None:
            grade = self._score_to_grade(quality_score)
            emoji = self._grade_to_emoji(grade)
            formatted_parts.append(f"{emoji} **Response Quality: {grade}** ({quality_score:.0f}/100)\n")
        
        # Add response
        formatted_parts.append(response)
        
        return "\n".join(formatted_parts)
    
    def _format_structured(self, response: str, quality_score: Optional[float]) -> str:
        """Format structured response with sections"""
        # Parse sections
        sections = self._parse_sections(response)
        
        formatted_parts = []
        
        # Add quality indicator
        if quality_score is not None:
            grade = self._score_to_grade(quality_score)
            emoji = self._grade_to_emoji(grade)
            formatted_parts.append(f"{emoji} **Quality: {grade}** ({quality_score:.0f}/100)\n")
        
        # Add separator
        formatted_parts.append("---\n")
        
        # Format each section
        for section_name, section_content in sections:
            icon = self._get_section_icon(section_name)
            formatted_parts.append(f"{icon} **{section_name}**\n")
            formatted_parts.append(section_content.strip() + "\n")
        
        return "\n".join(formatted_parts)
    
    def _format_analytical(self, response: str, quality_score: Optional[float]) -> str:
        """Format analytical response with emphasis on insights"""
        formatted_parts = []
        
        # Header
        formatted_parts.append("## 📊 Analysis Results\n")
        
        # Quality indicator
        if quality_score is not None:
            grade = self._score_to_grade(quality_score)
            emoji = self._grade_to_emoji(grade)
            formatted_parts.append(f"> {emoji} **Quality Score:** {grade} ({quality_score:.0f}/100)\n")
        
        # Main content
        formatted_parts.append(response)
        
        # Footer
        formatted_parts.append("\n---")
        formatted_parts.append("*Analysis completed with enhanced reasoning*")
        
        return "\n".join(formatted_parts)
    
    def _format_conversational(self, response: str) -> str:
        """Format conversational response"""
        # Keep it natural, minimal formatting
        return response
    
    def _parse_sections(self, response: str) -> List[Tuple[str, str]]:
        """Parse response into sections"""
        sections = []
        
        # Try different section patterns
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Check if line is a section header
            if self._is_section_header(line):
                # Save previous section
                if current_section:
                    sections.append((current_section, '\n'.join(current_content)))
                
                # Start new section
                current_section = self._extract_section_name(line)
                current_content = []
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        line = line.strip()
        
        # Check patterns
        patterns = [
            r'^#{1,3}\s+\w+',
            r'^\*\*[A-Z][^*]+\*\*',
            r'^[A-Z][A-Z\s]+:',
        ]
        
        return any(re.match(p, line) for p in patterns)
    
    def _extract_section_name(self, line: str) -> str:
        """Extract section name from header"""
        line = line.strip()
        
        # Remove markdown
        line = re.sub(r'^#+\s*', '', line)
        line = re.sub(r'\*\*', '', line)
        line = re.sub(r':', '', line)
        
        return line.strip().title()
    
    def _get_section_icon(self, section_name: str) -> str:
        """Get icon for section"""
        section_lower = section_name.lower()
        
        for key, icon in self.section_icons.items():
            if key in section_lower:
                return icon
        
        return "▪️"  # Default bullet
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _grade_to_emoji(self, grade: str) -> str:
        """Get emoji for grade"""
        grade_emojis = {
            "A": "🌟",
            "B": "✨",
            "C": "⭐",
            "D": "💫",
            "F": "⚠️"
        }
        return grade_emojis.get(grade, "📝")
    
    def format_with_quality_feedback(
        self,
        response: str,
        quality_score: Dict[str, Any]
    ) -> str:
        """
        Format response with detailed quality feedback
        
        Args:
            response: Response text
            quality_score: Quality score object from scorer
            
        Returns:
            Formatted response with quality details
        """
        formatted_parts = []
        
        # Main response
        formatted_parts.append(response)
        formatted_parts.append("\n---\n")
        
        # Quality breakdown
        overall = quality_score.get('overall_score', 0)
        grade = self._score_to_grade(overall)
        emoji = self._grade_to_emoji(grade)
        
        formatted_parts.append(f"### {emoji} Response Quality: {grade} ({overall:.0f}/100)\n")
        
        # Dimension scores
        dimensions = quality_score.get('dimension_scores', {})
        if dimensions:
            formatted_parts.append("**Quality Breakdown:**")
            for dim, score in dimensions.items():
                bar = self._create_progress_bar(score / 10)
                formatted_parts.append(f"- {dim.title()}: {bar} {score:.1f}/10")
        
        # Strengths
        strengths = quality_score.get('strengths', [])
        if strengths:
            formatted_parts.append("\n**✅ Strengths:**")
            for strength in strengths[:3]:
                formatted_parts.append(f"- {strength}")
        
        # Suggestions
        suggestions = quality_score.get('suggestions', [])
        if suggestions:
            formatted_parts.append("\n**💡 Improvement Suggestions:**")
            for suggestion in suggestions[:3]:
                formatted_parts.append(f"- {suggestion}")
        
        return "\n".join(formatted_parts)
    
    def _create_progress_bar(self, value: float, length: int = 10) -> str:
        """Create text progress bar"""
        filled = int(value * length)
        empty = length - filled
        return "█" * filled + "░" * empty


# Global instance
_response_formatter = None

def get_response_formatter() -> ResponseFormatter:
    """Get global response formatter instance"""
    global _response_formatter
    if _response_formatter is None:
        _response_formatter = ResponseFormatter()
    return _response_formatter
