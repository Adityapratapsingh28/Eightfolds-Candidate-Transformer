import pandas as pd
from typing import Any, Dict
from src.parsers.base import BaseParser
from src.utils.exceptions import ParserError

class CSVParser(BaseParser):
    """
    Parser for structured recruiter CSV files.
    """
    def parse(self, source_path: str) -> Dict[str, Any]:
        try:
            # Read CSV file using pandas
            df = pd.read_csv(source_path)
            # Replace NaN with None
            df = df.where(pd.notnull(df), None)
            
            # Convert rows to dictionaries
            records = df.to_dict(orient="records")
            
            return {
                "source_type": "csv",
                "source_path": source_path,
                "raw_content": records
            }
        except Exception as e:
            raise ParserError(f"Failed to parse CSV file at {source_path}: {e}") from e

