import pandas as pd
from openai import OpenAI
import json
from datetime import datetime
from typing import Dict, List
import os
from dotenv import load_dotenv

class SecurityCodeGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def read_security_csv(self, filepath: str) -> pd.DataFrame:
        return pd.read_csv(filepath)
    
    def generate_code_sample(self, description: str, language: str = "python") -> str:
        prompt = f"""
        Generate a code sample that demonstrates the security vulnerability described below:
        {description}
        
        Please provide the code in {language}.
        Include comments explaining the vulnerability.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a security expert providing code examples."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    def process_entries(self, df: pd.DataFrame) -> List[Dict]:
        results = []
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
                results.append(entry)
            except Exception as e:
                print(f"Error processing entry {row['id']}: {str(e)}")
                
        return results

def main():
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    csv_path = os.getenv('SECURITY_CSV_PATH')
    
    if not api_key or not csv_path:
        raise ValueError("Missing required environment variables")
    
    generator = SecurityCodeGenerator(api_key)
    df = generator.read_security_csv(csv_path)
    results = generator.process_entries(df)
    
    # Save results to JSON file
    with open('security_code_samples.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
