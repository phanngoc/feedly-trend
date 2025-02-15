
import re
import pandas as pd
from nltk.tokenize import sent_tokenize
from collections import Counter
import logging
from typing import List, Dict, Union
import nltk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self, threshold: int = 15):
        """
        Initialize TextCleaner with a threshold for repetitive sentences
        
        Args:
            threshold (int): Number of occurrences to consider a sentence as repetitive
        """
        self.threshold = threshold
        self._ensure_nltk_dependencies()
        
    @staticmethod
    def _ensure_nltk_dependencies():
        """Ensure required NLTK data is downloaded"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading required NLTK data...")
            nltk.download('punkt', quiet=True)

    @staticmethod
    def remove_special_chars(text: str) -> str:
        """
        Remove special characters and normalize whitespace
        
        Args:
            text (str): Input text
            
        Returns:
            str: Cleaned text
        """
        if not isinstance(text, str):
            return ""
            
        # Keep Vietnamese characters and basic punctuation
        text = re.sub(r'[^\s\w\.,!?\-áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợíìỉĩịúùủũụưứừửữựýỳỷỹỵđ]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def clean_dataframe(self, df: pd.DataFrame, text_column: str = 'text_content') -> pd.DataFrame:
        """
        Clean text data in a DataFrame
        
        Args:
            df (pd.DataFrame): Input DataFrame
            text_column (str): Name of the column containing text to clean
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        try:
            logger.info(f"Starting text cleaning process for column: {text_column}")
            
            # Create a copy to avoid modifying the original
            df_cleaned = df.copy()
            
            # Basic text cleaning
            df_cleaned[text_column] = df_cleaned[text_column].apply(self.remove_special_chars)
            df_cleaned[text_column] = df_cleaned[text_column].str.replace('\n', ' ')
            
            # Tokenize sentences
            df_cleaned['sentences'] = df_cleaned[text_column].apply(sent_tokenize)
            
            # Count sentence frequencies
            all_sentences = [sentence for sentences in df_cleaned['sentences'] for sentence in sentences if sentence]
            sentence_counts = Counter(all_sentences)
            
            # Remove repetitive sentences
            df_cleaned['filtered_sentences'] = df_cleaned['sentences'].apply(
                lambda sentences: [s for s in sentences if sentence_counts[s] < self.threshold]
            )
            
            # Join sentences back
            df_cleaned[text_column] = df_cleaned['filtered_sentences'].apply(' '.join)
            
            # Drop intermediate columns
            df_cleaned.drop(columns=['sentences', 'filtered_sentences'], inplace=True)
            
            logger.info("Text cleaning completed successfully")
            return df_cleaned
            
        except Exception as e:
            logger.error(f"Error during text cleaning: {str(e)}")
            raise

def main():
    """Main function to demonstrate usage"""
    try:
        # Example usage
        input_file = "link_spider_results.csv"
        output_file = "cleaned_link_spider_results.csv"
        
        logger.info(f"Reading input file: {input_file}")
        df = pd.read_csv(input_file)
        
        cleaner = TextCleaner(threshold=15)
        df_cleaned = cleaner.clean_dataframe(df)
        
        logger.info(f"Saving cleaned data to: {output_file}")
        df_cleaned.to_csv(output_file, index=False)
        
        logger.info("Process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
