from elasticsearch import Elasticsearch
import argparse
from typing import Dict, List, Optional
import json

class SecurityCodeSearcher:
    def __init__(self, es_host: str = "http://localhost:9201"):
        self.es = Elasticsearch([es_host])
        self.index_name = "security_code_samples"

    def get_sample_by_id(self, sample_id: str) -> Optional[Dict]:
        try:
            result = self.es.get(index=self.index_name, id=sample_id)
            return result['_source']
        except Exception as e:
            print(f"Error fetching sample {sample_id}: {str(e)}")
            return None

    def list_all_samples(self, size: int = 100) -> List[Dict]:
        query = {"query": {"match_all": {}}}
        results = self.es.search(index=self.index_name, body=query, size=size)
        return [hit['_source'] for hit in results['hits']['hits']]

    def search_by_tag(self, tag: str) -> List[Dict]:
        query = {
            "query": {
                "term": {
                    "metadata.tags.keyword": tag
                }
            }
        }
        results = self.es.search(index=self.index_name, body=query)
        return [hit['_source'] for hit in results['hits']['hits']]

def main():
    parser = argparse.ArgumentParser(description='Query security code samples')
    parser.add_argument('--action', choices=['get', 'list', 'search'], required=True)
    parser.add_argument('--id', help='Sample ID for get action')
    parser.add_argument('--tag', help='Tag to search for')
    parser.add_argument('--size', type=int, default=100, help='Number of results for list action')
    
    args = parser.parse_args()
    searcher = SecurityCodeSearcher()

    if args.action == 'get' and args.id:
        result = searcher.get_sample_by_id(args.id)
        if result:
            print(json.dumps(result, indent=2))
    elif args.action == 'list':
        results = searcher.list_all_samples(args.size)
        print(json.dumps(results, indent=2))
    elif args.action == 'search' and args.tag:
        results = searcher.search_by_tag(args.tag)
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

# python query_index.py --action get --id 19418
# python query_index.py --action list --size 10
# python query_index.py --action search --tag <tag_name>