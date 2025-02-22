import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Type definitions
class Column(TypedDict):
    name: str
    type: str

class Table(TypedDict):
    name: str
    columns: List[Column]

class Schema(TypedDict):
    tables: List[Table]

@dataclass
class TableMatch:
    name: str
    relevance_score: float
    columns: List[Column]
    match_reason: str

class SchemaAnalyzer:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize the SchemaAnalyzer with a specific sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.stopwords = {
            "show", "all", "and", "their", "get", "list", 
            "find", "me", "the", "with", "for", "in", "of"
        }

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from the query.
        
        Args:
            query: The input query string
            
        Returns:
            List of extracted keywords
        """
        # Extract words with 3+ letters and convert to lowercase
        words = re.findall(r'\b\w{3,}\b', query.lower())
        # Remove stopwords
        keywords = [word for word in words if word not in self.stopwords]
        return keywords

    def calculate_column_relevance(self, keywords: List[str], column: Column) -> float:
        """
        Calculate relevance score for a single column.
        
        Args:
            keywords: List of query keywords
            column: Column information
            
        Returns:
            Relevance score between 0 and 1
        """
        column_text = f"{column['name']} {column['type']}"
        column_embedding = self.model.encode(column_text)
        keywords_embedding = self.model.encode(" ".join(keywords))
        
        return float(cosine_similarity([column_embedding], [keywords_embedding])[0][0])

    def analyze_table_relevance(
        self, 
        table: Table, 
        keywords: List[str],
        query_embedding: np.ndarray
    ) -> Optional[TableMatch]:
        """
        Analyze the relevance of a table to the query.
        
        Args:
            table: Table information
            keywords: List of query keywords
            query_embedding: Embedding of the query
            
        Returns:
            TableMatch object if relevant, None otherwise
        """
        # Create a rich table description
        table_desc = (
            f"{table['name']} table containing "
            f"{', '.join(col['name'] for col in table['columns'])}"
        )
        table_embedding = self.model.encode(table_desc).reshape(1, -1)
        
        # Calculate base similarity score
        base_score = float(cosine_similarity(query_embedding, table_embedding)[0][0])
        
        # Calculate column-level relevance
        column_scores = [
            self.calculate_column_relevance(keywords, col)
            for col in table['columns']
        ]
        max_column_score = max(column_scores) if column_scores else 0
        
        # Combine scores with weights
        final_score = (base_score * 0.6) + (max_column_score * 0.4)
        
        # Only return tables with significant relevance
        if final_score > 0.5:
            match_reason = self._generate_match_reason(
                table['name'],
                table['columns'],
                final_score,
                keywords
            )
            return TableMatch(
                name=table['name'],
                relevance_score=final_score,
                columns=table['columns'],
                match_reason=match_reason
            )
        return None

    def _generate_match_reason(
        self,
        table_name: str,
        columns: List[Column],
        score: float,
        keywords: List[str]
    ) -> str:
        """Generate a human-readable explanation for why the table matched."""
        matching_columns = [
            col['name'] for col in columns
            if any(keyword in col['name'].lower() for keyword in keywords)
        ]
        
        if matching_columns:
            return (
                f"Table '{table_name}' matched with score {score:.2f} "
                f"due to relevant columns: {', '.join(matching_columns)}"
            )
        return (
            f"Table '{table_name}' matched with score {score:.2f} "
            f"based on semantic similarity to the query"
        )

    def find_relevant_tables(self, schema: Schema, query: str) -> Dict:
        """
        Find relevant tables in the schema based on the query.
        
        Args:
            schema: Database schema
            query: User's natural language query
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Extract keywords and create query embedding
            keywords = self.extract_keywords(query)
            query_embedding = self.model.encode(" ".join(keywords)).reshape(1, -1)
            
            # Analyze each table
            matches = []
            for table in schema['tables']:
                match = self.analyze_table_relevance(table, keywords, query_embedding)
                if match:
                    matches.append(match)
            
            # Sort matches by relevance score
            matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return {
                "query": query,
                "extracted_keywords": keywords,
                "matches": [
                    {
                        "table_name": match.name,
                        "relevance_score": round(match.relevance_score, 3),
                        "columns": match.columns,
                        "match_reason": match.match_reason
                    }
                    for match in matches
                ]
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing schema: {str(e)}")

def load_schema(file_path: str) -> Schema:
    """Load and validate database schema from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            schema = json.load(f)
            
        # Basic schema validation
        if not isinstance(schema, dict) or 'tables' not in schema:
            raise ValueError("Invalid schema format: missing 'tables' key")
            
        for table in schema['tables']:
            if not all(key in table for key in ['name', 'columns']):
                raise ValueError("Invalid table format: missing required keys")
                
        return schema
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")
    except Exception as e:
        raise Exception(f"Error loading schema: {str(e)}")

def main():
    """Main function to run the schema analyzer."""
    try:
        # Initialize analyzer
        analyzer = SchemaAnalyzer()
        
        # Get input from user
        file_path = input("Enter the path to your JSON schema file: ")
        schema = load_schema(file_path)
        
        while True:
            # Get query from user
            query = input("\nEnter your query (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
                
            # Analyze schema
            results = analyzer.find_relevant_tables(schema, query)
            
            # Print results
            print("\n=== Analysis Results ===")
            print(f"Query: {results['query']}")
            print(f"Keywords: {', '.join(results['extracted_keywords'])}")
            print("\nMatching Tables:")
            
            if results['matches']:
                for match in results['matches']:
                    print(f"\n📊 {match['table_name']}")
                    print(f"Relevance Score: {match['relevance_score']}")
                    print(f"Reason: {match['match_reason']}")
                    print("Columns:")
                    for col in match['columns']:
                        print(f"  - {col['name']} ({col['type']})")
            else:
                print("\n❌ No relevant tables found.")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()