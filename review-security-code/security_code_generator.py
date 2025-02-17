import pandas as pd
from openai import OpenAI
import json
from datetime import datetime
from typing import Dict, List
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

class SecurityCodeGenerator:
    def __init__(self, api_key: str, es_host: str = "http://localhost:9201"):
        self.client = OpenAI(api_key=api_key)
        self.es = Elasticsearch([es_host])
        self.index_name = "security_code_samples"
        
    def ensure_index_exists(self):
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "description": {"type": "text"},
                        "generated_code": {"type": "text"},
                        "metadata": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "platform": {"type": "keyword"},
                                "date_published": {"type": "date"},
                                "tags": {"type": "keyword"}
                            }
                        },
                        "generated_at": {"type": "date"}
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)
    
    def read_security_csv(self, filepath: str) -> pd.DataFrame:
        return pd.read_csv(filepath)
    
    def generate_code_sample(self, description: str, language: str = "python") -> str:
        prompt = f"""
        Generate ONLY the code sample (no explanations) that demonstrates the security vulnerability:
        {description}
        
        Return only valid {language} code with brief inline comments.
        Do not include any text before or after the code.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4-mini",
            messages=[
                {"role": "system", "content": "You are a code generator that returns only code samples with minimal inline comments."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def process_entries(self, df: pd.DataFrame, limit: int = None) -> List[Dict]:
        self.ensure_index_exists()
        results = []
                
        # Apply limit if specified
        if limit:
            df = df.head(limit)
            
        for _, row in df.iterrows():
            try:
                code_sample = self.generate_code_sample(row['description'])
                                
                entry = {
                    'id': row['id'],
                    'description': row['description'],
                    'generated_code': code_sample,
                    'metadata': {
                        'type': row['type'],
                        'platform': row['platform'],
                        'date_published': row['date_published'],
                        'tags': row['tags'].split(',') if isinstance(row['tags'], str) else [],
                                            },
                    'generated_at': datetime.now().isoformat()
                }
                
                # Update or create document in Elasticsearch
                self.es.index(
                    index=self.index_name,
                    id=entry['id'],
                    body=entry,
                    op_type='index'  # This will update if exists or create if not
                )
                
                results.append(entry)
                print(f"Updated/created entry {row['id']}")
                print(f"Successfully indexed entry {row['id']}")
                
            except Exception as e:
                print(f"Error processing entry {row['id']}: {str(e)}")
                
        return results

def main():
    from dotenv import dotenv_values
    config = dotenv_values('../.env')
    print('config:', config)
    api_key = config.get('OPENAI_API_KEY')
    csv_path = config.get('SECURITY_CSV_PATH')
    print('api_key:', api_key, 'csv_path:', csv_path)
    if not api_key or not csv_path:
        raise ValueError("Missing required environment variables")
    
    generator = SecurityCodeGenerator(api_key)
    df = generator.read_security_csv(csv_path)
    results = generator.process_entries(df, limit=10)
    
    # Save results to JSON file
    with open('security_code_samples.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
