"""
Knowledge Base Manager for Vishleshak AI v1
Manages domain-specific knowledge loading and updates
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from rag.vector_store import get_vector_store
from rag.document_loader import DocumentProcessor
from config import rag_config

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """
    Manages domain-specific knowledge base
    
    Features:
    - Load knowledge from files
    - Organize by domain
    - Update and maintain knowledge
    - Query domain-specific information
    
    Usage:
        kb_manager = KnowledgeBaseManager()
        kb_manager.load_all_knowledge()
        kb_manager.add_knowledge_from_text(text, domain="education")
    """
    
    def __init__(self):
        """Initialize knowledge base manager"""
        self.vector_store = get_vector_store()
        self.document_processor = DocumentProcessor()
        self.base_path = rag_config.KNOWLEDGE_BASE_DIR
        logger.info("✅ Knowledge base manager initialized")
    
    def load_domain_knowledge(self, domain: str) -> int:
        """
        Load all knowledge for a specific domain
        
        Args:
            domain: Domain name (education, finance, general)
            
        Returns:
            Number of knowledge pieces loaded
        """
        domain_path = rag_config.KNOWLEDGE_BASE_DOMAINS.get(domain)
        
        if not domain_path or not domain_path.exists():
            logger.warning(f"Domain path not found: {domain}")
            return 0
        
        logger.info(f"Loading knowledge for domain: {domain}")
        
        # Load all documents from domain directory
        documents = self.document_processor.load_directory(domain_path)
        
        if not documents:
            logger.info(f"No documents found for domain: {domain}")
            return 0
        
        # Chunk documents
        chunks = self.document_processor.chunk_documents(documents)
        
        # Add to vector store
        count = 0
        for chunk in chunks:
            # Add domain to metadata
            chunk.metadata["domain"] = domain
            
            try:
                self.vector_store.add_knowledge(
                    knowledge_text=chunk.page_content,
                    metadata=chunk.metadata
                )
                count += 1
            except Exception as e:
                logger.error(f"Error adding knowledge chunk: {e}")
        
        logger.info(f"✅ Loaded {count} knowledge pieces for {domain}")
        return count
    
    def load_all_knowledge(self) -> Dict[str, int]:
        """
        Load knowledge from all domains
        
        Returns:
            Dict mapping domain to count of loaded pieces
        """
        logger.info("Loading all domain knowledge...")
        
        results = {}
        for domain in rag_config.KNOWLEDGE_BASE_DOMAINS.keys():
            count = self.load_domain_knowledge(domain)
            results[domain] = count
        
        total = sum(results.values())
        logger.info(f"✅ Loaded total of {total} knowledge pieces")
        return results
    
    def add_knowledge_from_text(
        self, 
        text: str,
        domain: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add knowledge from text string
        
        Args:
            text: Knowledge text
            domain: Domain name
            metadata: Additional metadata
            
        Returns:
            ID of added knowledge
        """
        if metadata is None:
            metadata = {}
        
        metadata["domain"] = domain
        metadata["source"] = "manual_entry"
        
        return self.vector_store.add_knowledge(text, metadata)
    
    def add_knowledge_from_file(
        self, 
        file_path: Path,
        domain: str
    ) -> int:
        """
        Add knowledge from a file
        
        Args:
            file_path: Path to file
            domain: Domain name
            
        Returns:
            Number of knowledge pieces added
        """
        documents = self.document_processor.load_file(file_path)
        
        if not documents:
            return 0
        
        chunks = self.document_processor.chunk_documents(documents)
        
        count = 0
        for chunk in chunks:
            chunk.metadata["domain"] = domain
            
            try:
                self.vector_store.add_knowledge(
                    knowledge_text=chunk.page_content,
                    metadata=chunk.metadata
                )
                count += 1
            except Exception as e:
                logger.error(f"Error adding knowledge: {e}")
        
        logger.info(f"Added {count} knowledge pieces from {file_path.name}")
        return count
    
    def create_default_knowledge(self):
        """Create default knowledge files if they don't exist"""
        logger.info("Creating default knowledge files...")
        
        # Education domain default knowledge
        education_knowledge = """
# Student Dropout Prevention Best Practices

## Early Warning Systems
Early intervention is crucial. Research shows that identifying at-risk students 
within the first 2-3 weeks of a semester can reduce dropout rates by 30-40%.

Key indicators of dropout risk:
- Attendance below 70%
- 3 or more consecutive absences
- Failing grades in first month
- Low engagement in class activities

## Effective Interventions

### 1. Peer Mentoring
Studies show peer mentoring programs increase retention by 15-25%.
- Pair at-risk students with successful peers
- Weekly check-ins
- Cost: $50-100 per student
- ROI: High

### 2. Academic Support
Tutoring and academic support services are highly effective.
- Individual tutoring
- Study groups
- Office hours accessibility
- Retention improvement: 20-30%

### 3. Financial Support
Financial issues account for 40% of dropouts.
- Emergency grants
- Work-study programs
- Scholarship opportunities

## National Benchmarks
- Average dropout rate (community college): 12.8%
- Top-performing institutions: 8-10%
- National average (4-year): 8.5%

Source: National Center for Education Statistics (NCES), 2023
"""
        
        # Finance domain default knowledge
        finance_knowledge = """
# Financial Data Analysis Best Practices

## Key Financial Metrics

### Profitability Ratios
- Gross Profit Margin = (Revenue - COGS) / Revenue
- Net Profit Margin = Net Income / Revenue
- Return on Assets (ROA) = Net Income / Total Assets
- Return on Equity (ROE) = Net Income / Shareholder Equity

### Liquidity Ratios
- Current Ratio = Current Assets / Current Liabilities
- Quick Ratio = (Current Assets - Inventory) / Current Liabilities
- Cash Ratio = Cash / Current Liabilities

### Efficiency Ratios
- Asset Turnover = Revenue / Average Total Assets
- Inventory Turnover = COGS / Average Inventory

## Industry Benchmarks
Financial ratios vary significantly by industry. Always compare to industry peers.

## Data Quality
- Verify data accuracy
- Check for outliers
- Ensure consistency
- Validate calculations

Source: Financial Analysis Standards Board
"""
        
        # General domain default knowledge
        general_knowledge = """
# Data Analysis Best Practices

## Statistical Analysis Guidelines

### Choosing the Right Analysis
1. Descriptive Statistics: Summarize data (mean, median, std)
2. Inferential Statistics: Make predictions and inferences
3. Correlation Analysis: Identify relationships
4. Regression Analysis: Model relationships

### Data Quality Checks
- Missing data assessment
- Outlier detection
- Distribution analysis
- Normality tests

### Sample Size Considerations
- Minimum 30 samples for meaningful statistics
- Larger samples for rare events
- Power analysis for hypothesis testing

## Visualization Best Practices
- Choose appropriate chart types
- Label axes clearly
- Use color meaningfully
- Avoid misleading scales

## Common Pitfalls
- Correlation vs causation
- Simpson's paradox
- Survivorship bias
- Selection bias

Source: Statistical Analysis Standards
"""
        
        # Create files
        knowledge_to_create = [
            ("education", "dropout_prevention.txt", education_knowledge),
            ("finance", "financial_metrics.txt", finance_knowledge),
            ("general", "data_analysis_best_practices.txt", general_knowledge)
        ]
        
        for domain, filename, content in knowledge_to_create:
            domain_path = rag_config.KNOWLEDGE_BASE_DOMAINS[domain]
            file_path = domain_path / filename
            
            if not file_path.exists():
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Created: {file_path}")
                except Exception as e:
                    logger.error(f"Error creating {file_path}: {e}")


# Global instance
_kb_manager = None

def get_knowledge_base_manager() -> KnowledgeBaseManager:
    """Get global knowledge base manager instance"""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
    return _kb_manager
