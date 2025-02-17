import argparse
import os
import git
from elasticsearch import Elasticsearch
from openai import OpenAI
from code_reviewer import CodeReviewer
from typing import Optional, Tuple

def load_git_diff(repo_path: str, commit_hash: Optional[str] = None) -> Tuple[str, str]:
    """Load git diff from repository"""
    repo = git.Repo(repo_path)
    
    if commit_hash:
        # Get specific commit
        commit = repo.commit(commit_hash)
        parent = commit.parents[0] if commit.parents else None
        
        if parent:
            # Get changes between parent and current commit
            diffs = parent.diff(commit)
            if not diffs:
                raise ValueError("No changes found in commit")
            
            # Get the first changed file
            diff = diffs[0]
            # Get old version
            old_blob = parent.tree[diff.a_path] if diff.a_path else None
            old_code = old_blob.data_stream.read().decode('utf-8') if old_blob else ""
            
            # Get new version
            new_blob = commit.tree[diff.b_path] if diff.b_path else None
            new_code = new_blob.data_stream.read().decode('utf-8') if new_blob else ""
        else:
            # First commit - compare with empty string
            diffs = commit.diff(git.NULL_TREE)
            if not diffs:
                raise ValueError("No changes found in first commit")
            
            diff = diffs[0]
            old_code = ""
            new_blob = commit.tree[diff.b_path]
            new_code = new_blob.data_stream.read().decode('utf-8')
    else:
        # Get working directory changes
        diff_index = repo.index.diff(None)
        
        if not diff_index:
            raise ValueError("No changes found in working directory")
        
        # Get the first changed file
        change = diff_index[0]
        if change.a_blob:
            old_code = change.a_blob.data_stream.read().decode('utf-8')
        else:
            old_code = ""
        
        # Read current version from disk
        with open(os.path.join(repo_path, change.b_path), 'r') as f:
            new_code = f.read()
            
    return old_code, new_code

def main():
    parser = argparse.ArgumentParser(description='Code Review Tool')
    parser.add_argument('--path', required=True, help='Path to the git repository')
    parser.add_argument('--commit', help='Specific commit hash to review')
    parser.add_argument('--es-host', default='localhost', help='Elasticsearch host')
    parser.add_argument('--es-port', default=9200, type=int, help='Elasticsearch port')
    parser.add_argument('--openai-key', required=True, help='OpenAI API key')
    
    args = parser.parse_args()
    
    # Initialize clients
    es_client = Elasticsearch(['http://localhost:9201'])
    openai_client = OpenAI(api_key=args.openai_key)
    
    # Initialize reviewer
    reviewer = CodeReviewer(es_client, openai_client)
    
    try:
        # Load git diff
        old_code, new_code = load_git_diff(args.path, args.commit)
        
        # Perform review
        result = reviewer.review_code(old_code, new_code)
        
        # Print results
        print("\n=== Code Review Results ===")
        print(f"\nQuality Score: {result.quality_score:.2f}")
        
        print("\nCodeBERT Analysis:")
        for label, score in result.codebert_scores.items():
            print(f"- {label}: {score:.2f}")
        
        print("\nReview Comments:")
        for comment in result.suggested_comments:
            print(f"- {comment}")
            
        print("\nSuggested Refinements:")
        for refinement in result.suggested_refinements:
            print(f"- {refinement}")
            
        print("\nSecurity Risks:")
        for risk in result.security_risks:
            print(f"- Type: {risk['risk_type']}")
            print(f"  Description: {risk['description']}")
            print(f"  Similarity Score: {risk['similarity_score']:.2f}")
            
        print("\nDiff Analysis:")
        print(f"Lines Added: {result.diff_analysis['lines_added']}")
        print(f"Lines Removed: {result.diff_analysis['lines_removed']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())

# python review_command.py --path /Users/ngocp/Documents/projects/mrmax  --commit bb9d6307bf5b20c54a2d9013d6d8764642f284cf --es-host http://localhost --es-port 9201 --openai-key {openai_key}