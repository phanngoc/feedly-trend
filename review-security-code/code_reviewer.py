import torch
from typing import Dict, List, Optional
from dataclasses import dataclass
from elasticsearch import Elasticsearch
import difflib
from openai import OpenAI
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification
)

@dataclass
class ReviewResult:
    quality_score: float
    codebert_scores: Dict[str, float]  # Add CodeBERT scores
    suggested_comments: List[str]
    suggested_refinements: List[str]
    security_risks: List[Dict]
    diff_analysis: Dict

class CodeReviewer:
    def __init__(self, es_client: Elasticsearch, openai_client: OpenAI):
        self.es = es_client
        self.openai = openai_client
        self.security_index = "security_code_samples"
        
        # Initialize CodeBERT model with 2 classes (good/bad)
        self.codebert_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.codebert_model = AutoModelForSequenceClassification.from_pretrained(
            "microsoft/codebert-base",
            num_labels=2  # Binary classification
        )
        self.codebert_model.eval()

    def analyze_diff(self, old_code: str, new_code: str) -> Dict:
        """Analyze git diff between old and new code versions"""
        diff = list(difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True)
        ))
        
        return {
            "diff": "".join(diff),
            "lines_added": len([l for l in diff if l.startswith("+")]),
            "lines_removed": len([l for l in diff if l.startswith("-")]),
        }

    def estimate_quality(self, code: str) -> float:
        """Estimate code quality score based on various metrics"""
        prompt = f"""
        Analyze this code and rate its quality from 0-1 based on:
        - Code readability
        - Best practices
        - Potential bugs
        - Security considerations
        
        Code to analyze:
        {code}
        
        Return only the numeric score between 0 and 1.
        """
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You analyze code quality and return only a numeric score between 0 and 1."},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 0.5  # Default score if parsing fails

    def generate_comments(self, diff: str) -> List[str]:
        """Generate review comments based on code changes"""
        prompt = f"""
        Review this code diff and provide specific, actionable comments about:
        - Potential issues
        - Style improvements
        - Best practices
        - Security concerns
        
        Diff to review:
        {diff}
        
        Return a list of clear, concise review comments.
        """
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an experienced code reviewer providing specific, actionable feedback."},
                {"role": "user", "content": prompt}
            ]
        )
        
        comments = response.choices[0].message.content.strip().split("\n")
        return [c.strip("- ") for c in comments if c.strip()]

    def suggest_refinements(self, code: str) -> List[str]:
        """Suggest code refinements and improvements"""
        prompt = f"""
        Analyze this code and suggest specific improvements for:
        - Code quality
        - Performance
        - Security
        - Best practices
        
        Code to analyze:
        {code}
        
        Return a list of specific code refinement suggestions.
        """
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You suggest specific code improvements and refinements."},
                {"role": "user", "content": prompt}
            ]
        )
        
        refinements = response.choices[0].message.content.strip().split("\n")
        return [r.strip("- ") for r in refinements if r.strip()]

    def check_security_risks(self, code: str) -> List[Dict]:
        """Check for potential security risks using the security samples index"""
        # Search for similar security vulnerabilities
        response = self.es.search(
            index=self.security_index,
            body={
                "query": {
                    "multi_match": {
                        "query": code,
                        "fields": ["description", "generated_code"]
                    }
                }
            }
        )
        
        risks = []
        for hit in response["hits"]["hits"]:
            risks.append({
                "risk_type": hit["_source"]["metadata"]["type"],
                "description": hit["_source"]["description"],
                "similarity_score": hit["_score"]
            })
            
        return risks

    def analyze_codebert(self, code: str) -> Dict[str, float]:
        """Analyze code quality using CodeBERT"""
        inputs = self.codebert_tokenizer(
            code, 
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.codebert_model(**inputs)
        
        scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
        labels = ["Needs Improvement", "Good"]  # Binary classification labels
        
        analysis = {labels[i]: float(scores[0][i]) for i in range(len(labels))}
        
        # Add a derived "Risk Level" score
        risk_score = 1 - analysis["Good"]  # Higher risk when code quality is lower
        analysis["Risk Level"] = risk_score
        
        return analysis

    def synthesize_review_comments(self, 
                                 codebert_scores: Dict[str, float],
                                 comments: List[str],
                                 refinements: List[str],
                                 security_risks: List[Dict]) -> List[str]:
        """Synthesize and improve review comments using AI"""
        
        # Update context to include risk level
        context = f"""
        Code Analysis Results:
        Code Quality: {codebert_scores.get('Good', 0):.2f}
        Risk Level: {codebert_scores.get('Risk Level', 0):.2f}
        
        Current Comments:
        {chr(10).join(f'- {c}' for c in comments)}
        
        Suggested Refinements:
        {chr(10).join(f'- {r}' for r in refinements)}
        
        Security Risks:
        {chr(10).join(f'- {r["risk_type"]}: {r["description"]}' for r in security_risks)}
        
        Please analyze these review results and provide:
        1. Synthesized, non-redundant comments
        2. Prioritized recommendations based on risk level
        3. Clear action items
        4. Risk assessment summary
        
        Return the improved review comments as a list, one item per line.
        """
        
        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer who synthesizes and improves code review feedback."},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract and clean up the synthesized comments
        synthesized = response.choices[0].message.content.strip().split('\n')
        return [comment.strip('- ').strip() for comment in synthesized if comment.strip()]

    def review_code(self, old_code: str, new_code: str) -> ReviewResult:
        """Perform comprehensive code review"""
        # Analyze diff
        diff_analysis = self.analyze_diff(old_code, new_code)
        
        # Get CodeBERT analysis
        codebert_scores = self.analyze_codebert(new_code)
        
        # Get analysis results
        quality_score = self.estimate_quality(new_code)
        initial_comments = self.generate_comments(diff_analysis["diff"])
        refinements = self.suggest_refinements(new_code)
        security_risks = self.check_security_risks(new_code)
        
        # Synthesize and improve the review comments
        improved_comments = self.synthesize_review_comments(
            codebert_scores=codebert_scores,
            comments=initial_comments,
            refinements=refinements,
            security_risks=security_risks
        )
        
        return ReviewResult(
            quality_score=quality_score,
            codebert_scores=codebert_scores,
            suggested_comments=improved_comments,
            suggested_refinements=refinements, 
            security_risks=security_risks,
            diff_analysis=diff_analysis
        )
