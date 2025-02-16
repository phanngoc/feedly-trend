from typing import List, Dict
import json
from datetime import datetime
import elasticsearch
from elasticsearch import Elasticsearch

class CodeSearchIndex:
    def __init__(self, es_host: str = "localhost:9200"):
        self.es = Elasticsearch([es_host])
        self.index_name = "security_code_samples"
        
    def create_index(self):
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
    # Load generated samples
    with open('security_code_samples.json', 'r') as f:
        samples = json.load(f)
    
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
