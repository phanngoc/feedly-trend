from typing import List, Dict
import json
from datetime import datetime
import elasticsearch
from elasticsearch import Elasticsearch
import csv

class CodeSearchIndex:
    def __init__(self, es_host: str = "http://localhost:9201"):
        self.es = Elasticsearch([es_host])
        self.index_name = "security_code_samples"
        
    def create_index(self):
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
    
    def index_samples(self, samples: List[Dict]):
        for sample in samples:
            # Check if the document already exists
            if not self.es.exists(index=self.index_name, id=sample['id']):
                self.es.index(
                    index=self.index_name,
                    id=sample['id'],
                    body=sample
                )
    def search_code_samples(self, query: str, filters: Dict = None) -> List[Dict]:
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["description", "generated_code", "metadata.tags"]
                            }
                        }
                    ]
                }
            }
        }
        
        if filters:
            search_body["query"]["bool"]["filter"] = []
            for key, value in filters.items():
                search_body["query"]["bool"]["filter"].append(
                    {"term": {key: value}}
                )
        
        results = self.es.search(
            index=self.index_name,
            body=search_body
        )
        
        return [hit["_source"] for hit in results["hits"]["hits"]]

def main():
    data_csv_file = 'vulnerability_dataset.csv'
    # Load generated samples
    samples = []
    with open(data_csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = {
                "id": row["id"],
                "description": row["description"],
                "generated_code": "",  # Assuming generated code is not in the CSV
                "metadata": {
                    "type": row["type"],
                    "platform": row["platform"],
                    "date_published": row["date_published"],
                    "tags": row["tags"].split(';') if row["tags"] else []
                },
                "generated_at": datetime.now().isoformat()
            }
            samples.append(sample)
    
    # Index samples
    searcher = CodeSearchIndex()
    searcher.create_index()
    searcher.index_samples(samples)
    
    # Example search
    results = searcher.search_code_samples(
        query="sql injection",
        filters={"metadata.platform": "web"}
    )
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
