import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET

class VulnerabilityDataCollector:
    def __init__(self):
        self.nvd_api_key = os.getenv('NVD_API_KEY')
        self.feedly_api_key = os.getenv('FEEDLY_API_KEY')
        self.session = self._create_session()
        self.logging_setup()

    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def logging_setup(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def validate_date(self, days_back: int) -> str:
        """Validate and return proper date format for NVD API"""
        today = datetime.now()
        if days_back > 365:  # NVD typically limits historical data
            days_back = 365
        start_date = (today - timedelta(days=days_back))
        return start_date.strftime("%Y-%m-%dT%H:%M:%S.000")

    def collect_nvd_data(self, days_back: int = 30) -> List[Dict]:
        """Collect vulnerability data from NVD with proper date handling"""
        start_date = self.validate_date(days_back)
        base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        params = {
            "pubStartDate": start_date,
            "resultsPerPage": 2000
        }
        
        headers = {
            "apiKey": self.nvd_api_key
        } if self.nvd_api_key else {}

        try:
            # Add rate limiting
            time.sleep(6)  # NVD rate limit is 5 requests per 30 seconds
            response = self.session.get(
                base_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 403:
                logging.error("NVD API key invalid or rate limit exceeded")
                return []
            
            response.raise_for_status()
            data = response.json()
            return data.get('vulnerabilities', [])
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error collecting NVD data: {str(e)}")
            return []

    def collect_exploitdb_data(self) -> List[Dict]:
        """Collect exploit data from Exploit-DB with updated URL"""
        url = "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv"
        backup_url = "https://www.exploit-db.com/download/files_exploits.csv"
        
        try:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                content = response.content
            except:
                logging.warning("Primary ExploitDB URL failed, trying backup...")
                response = self.session.get(backup_url, timeout=30)
                response.raise_for_status()
                content = response.content
                
            df = pd.read_csv(pd.io.common.BytesIO(content))
            return df.to_dict('records')
        except Exception as e:
            logging.error(f"Error collecting ExploitDB data: {str(e)}")
            return []

    def _parse_cwe_xml(self, xml_path: str) -> pd.DataFrame:
        """Parse CWE XML file and convert to DataFrame"""
        try:
            # Parse XML file
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract weakness data
            weaknesses = []
            for weakness in root.findall('.//Weakness'):
                weakness_data = {
                    'cwe_id': weakness.get('ID'),
                    'name': weakness.get('Name'),
                    'abstraction': weakness.get('Abstraction'),
                    'status': weakness.get('Status'),
                }
                
                # Get description
                desc = weakness.find('Description')
                if desc is not None:
                    weakness_data['description'] = desc.text
                
                # Get extended description
                ext_desc = weakness.find('Extended_Description')
                if ext_desc is not None:
                    weakness_data['extended_description'] = ''.join(ext_desc.itertext()).strip()
                
                # Get likelihood
                likelihood = weakness.find('Likelihood_Of_Exploit')
                if likelihood is not None:
                    weakness_data['likelihood'] = likelihood.text
                
                weaknesses.append(weakness_data)
            
            return pd.DataFrame(weaknesses)
            
        except Exception as e:
            logging.error(f"Error parsing CWE XML: {str(e)}")
            return pd.DataFrame()

    def collect_cwe_data(self) -> Dict:
        """Collect CWE data with better error handling"""
        try:
            # Add rate limiting
            time.sleep(2)
            response = self.session.get(
                "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip",
                timeout=30
            )
            response.raise_for_status()
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Extract zip content
            zip_content = BytesIO(response.content)
            with zipfile.ZipFile(zip_content) as zip_ref:
                xml_filename = zip_ref.namelist()[0]
                extracted_path = os.path.join(data_dir, xml_filename)
                zip_ref.extract(xml_filename, data_dir)
            
            # Parse XML and convert to DataFrame
            cwe_df = self._parse_cwe_xml(extracted_path)
            
            return {
                "cwe_xml_path": extracted_path,
                "cwe_data": cwe_df.to_dict('records') if not cwe_df.empty else []
            }
            
        except Exception as e:
            logging.error(f"Error collecting CWE data: {str(e)}")
            return {}

    def collect_feedly_data(self, keywords: List[str]) -> List[Dict]:
        """Collect threat intelligence from Feedly"""
        if not self.feedly_api_key:
            logging.warning("Feedly API key not found")
            return []

        url = "https://cloud.feedly.com/v3/streams/contents"
        headers = {"Authorization": f"Bearer {self.feedly_api_key}"}
        
        try:
            all_articles = []
            for keyword in keywords:
                params = {
                    "streamId": f"feed/http://feeds.feedburner.com/security/{keyword}",
                    "count": 100
                }
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                articles = response.json().get('items', [])
                all_articles.extend(articles)
            return all_articles
        except Exception as e:
            logging.error(f"Error collecting Feedly data: {e}")
            return []

    def merge_data(self) -> pd.DataFrame:
        """Merge data from all sources into a single DataFrame"""
        nvd_data = self.collect_nvd_data()
        if not nvd_data:
            logging.warning("No NVD data collected")
            
        exploit_data = self.collect_exploitdb_data()
        if not exploit_data:
            logging.warning("No ExploitDB data collected")
            
        cwe_result = self.collect_cwe_data()
        cwe_data = cwe_result.get('cwe_data', [])

        # Create DataFrame and perform necessary transformations
        df = pd.DataFrame(exploit_data) if exploit_data else pd.DataFrame()
        
        # Convert NVD data to DataFrame
        nvd_df = pd.json_normalize(nvd_data) if nvd_data else pd.DataFrame()
        
        # Convert CWE data to DataFrame
        cwe_df = pd.DataFrame(cwe_data) if cwe_data else pd.DataFrame()
        
        # Merge NVD data with ExploitDB data if both exist
        if not nvd_df.empty and not df.empty:
            df = df.merge(nvd_df, how='outer', left_on='id', right_on='cve.id', suffixes=('_exploit', '_nvd'))
        elif not nvd_df.empty:
            df = nvd_df
            
        # Merge CWE data if exists
        if not cwe_df.empty and 'cwe_id' in cwe_df.columns:
            # Look for CWE references in the existing data
            cwe_columns = [col for col in df.columns if 'cwe' in col.lower()]
            if cwe_columns:
                # Assuming the first CWE reference column found is the one to join on
                cwe_ref_col = cwe_columns[0]
                logging.info(f"Merging CWE data using column: {cwe_ref_col}")
                df = df.merge(
                    cwe_df, 
                    how='left',
                    left_on=cwe_ref_col,
                    right_on='cwe_id',
                    suffixes=('', '_cwe')
                )
            else:
                logging.warning("No CWE reference column found in vulnerability data")
                # Append CWE data as new rows if no join possible
                df = pd.concat([df, cwe_df], ignore_index=True)

        # Drop duplicate rows if any
        df.drop_duplicates(inplace=True)
        
        logging.info(f"Final DataFrame columns: {df.columns.tolist()}")
        return df

    def save_data(self, df: pd.DataFrame, filename: str = "vulnerability_dataset.csv"):
        """Save the collected data to a CSV file"""
        try:
            df.to_csv(filename, index=False)
            logging.info(f"Data saved successfully to {filename}")
        except Exception as e:
            logging.error(f"Error saving data: {e}")

def main():
    collector = VulnerabilityDataCollector()
    df = collector.merge_data()
    collector.save_data(df)

if __name__ == "__main__":
    main()
