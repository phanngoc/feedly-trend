from bs4 import BeautifulSoup
import re

class TextCleaner:
    @staticmethod
    def remove_html_tags(text):
        """Loại bỏ tất cả HTML tags"""
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text(separator=' ')
    
    @staticmethod
    def remove_special_chars(text):
        """Loại bỏ ký tự đặc biệt và chuẩn hóa khoảng trắng"""
        # Giữ lại chữ tiếng Việt và dấu câu cơ bản
        text = re.sub(r'[^\s\w\.,!?\-áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợíìỉĩịúùủũụưứừửữựýỳỷỹỵđ]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def remove_common_sections(text):
        """Loại bỏ các phần nội dung phổ biến như header, footer, menu"""
        common_patterns = [
            r'Tin theo khu vực.*?International',
            r'Trang chủ.*?Tất cả',
            r'\[ Mới nhất \].*?\[.*?\]',
            r'javascript:;.*?Lên đầu trang',
            r'VnExpress App.*?Google Play'
        ]
        
        for pattern in common_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        return text
    
    @staticmethod
    def extract_main_content(text):
        """Trích xuất phần nội dung chính, loại bỏ các phần sidebar"""
        # Tìm đoạn text có độ dài lớn nhất giữa các [...] hoặc các đoạn văn
        paragraphs = re.split(r'\[|\]|\n{2,}', text)
        if not paragraphs:
            return text
            
        # Lấy đoạn có độ dài lớn nhất và có ý nghĩa
        main_content = max(paragraphs, key=lambda x: len(x.strip()) if len(x.strip()) > 50 else 0)
        return main_content.strip()
    
    @staticmethod
    def clean_text(text):
        """Thực hiện tất cả các bước làm sạch text"""
        text = TextCleaner.remove_html_tags(text)
        text = TextCleaner.remove_common_sections(text)
        text = TextCleaner.extract_main_content(text)
        text = TextCleaner.remove_special_chars(text)
        return text
