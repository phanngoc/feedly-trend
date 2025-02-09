import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import unicodedata
from text_cleaner import TextCleaner

def normalize_text(text):
    # Chuẩn hóa unicode
    text = unicodedata.normalize('NFKC', text)
    # Loại bỏ các ký tự đặc biệt
    text = re.sub(r'[^\s\wáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợíìỉĩịúùủũụưứừửữựýỳỷỹỵđ_]', ' ', text)
    # Chuẩn hóa khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def remove_similar_posts(df, similarity_threshold=0.8):
    # Làm sạch nội dung text trước khi so sánh
    df['cleaned_content'] = df['text_content'].apply(TextCleaner.clean_text)
    
    # Chuẩn hóa tiêu đề
    normalized_titles = df['title'].apply(normalize_text)
    
    # Tạo TF-IDF vectors từ cả tiêu đề và nội dung đã làm sạch
    vectorizer = TfidfVectorizer(min_df=1)
    tfidf_matrix = vectorizer.fit_transform(normalized_titles + ' ' + df['cleaned_content'])
    
    # Tính cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Tìm các cặp bài viết tương tự
    duplicate_indices = set()
    for i in range(len(cosine_sim)):
        for j in range(i + 1, len(cosine_sim)):
            if cosine_sim[i][j] > similarity_threshold:
                # Giữ lại bài có tiêu đề dài hơn
                if len(df.iloc[i]['title']) < len(df.iloc[j]['title']):
                    duplicate_indices.add(i)
                else:
                    duplicate_indices.add(j)
    
    # Loại bỏ các bài trùng lặp
    unique_df = df.drop(index=list(duplicate_indices))
    print(f"\nĐã loại bỏ {len(duplicate_indices)} bài viết trùng lặp")
    
    # Xóa cột cleaned_content tạm thời
    unique_df = unique_df.drop('cleaned_content', axis=1)
    return unique_df

def analyze_csv():
    # Đọc file CSV
    df = pd.read_csv('rss_crawler/output/link_spider_results.csv')
    
    print("\nSố lượng bài viết ban đầu:", len(df))
    
    # Loại bỏ các bài viết tương tự
    unique_df = remove_similar_posts(df)
    
    print("Số lượng bài viết sau khi lọc:", len(unique_df))
    
    print("\nCác tiêu đề còn lại sau khi lọc:")
    for title in unique_df['title']:
        print(f"- {title}")
        
    # Lưu kết quả đã lọc
    unique_df.to_csv('rss_crawler/output/unique_posts.csv', index=False)

def main():
    analyze_csv()

if __name__ == "__main__":
    main()

