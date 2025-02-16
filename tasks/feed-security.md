
# Phân tích tính năng và cơ chế hoạt động của ứng dụng: Tổng hợp tin tức tự động với AI

Hôm nay mình tìm thấy một tool về AI trong việc tổng hợp tin tức, giúp tổng hợp nhanh các bài viết, tự động phân tích bài viết để tìm ra thông tin quan trọng và cá nhân hóa nội dung để phục vụ độc giả. 

Công cụ này nằm trong gói Feedly Market Intelligence.
https://feedly.com/customers/posts/airbus-cybersecurity-case-study

Mình thử tìm hiểu cơ chế hoạt động của công cụ này, có hỏi chatgpt suggest một số cách mà có lẽ app trên đã sử dụng.

> Chống chỉ định: mình chỉ tìm hiểu mô phỏng, không chắc application đó sử dụng nhe.

Chúng ta huấn luyện một mô hình hồi quy để dự đoán điểm CVSS.

Các hướng dùng ML Models for Prediction
- Random Forest Regressor (Good for structured data).
- XGBoost (Performs well with missing values and non-linearity).
- Deep Learning (Transformer-based model) (If using full-text embeddings).

## **Implementing CVSS Score Prediction using Machine Learning**  

### **1️⃣ Step 1: Nghĩ cách collect data, một vấn đề không phải dễ :D **  

Cái gì cũng phải liên quan tới score, độ khó cũng liên tới score, nên cần phải có data từ nhiều nguồn để train model.


| **Nguồn**          | **Chi tiết** |
|--------------------|--------------|
| **NVD (Cơ sở dữ liệu lỗ hổng quốc gia)** | Cung cấp mô tả CVE, điểm CVSS (nếu có), và ánh xạ CWE. |
| **ExploitDB** | Chứa thông tin về khả năng khai thác thực tế, chỉ ra nếu một lỗ hổng đang bị khai thác. |
| **MITRE CWE** | Phân loại các lỗ hổng vào các danh mục (ví dụ: tràn bộ đệm, tiêm nhiễm). |
| **Feedly Threat Intelligence** | Cung cấp xu hướng an ninh mạng theo thời gian thực và các vector tấn công ước tính bằng AI. |

📌 **Example Dataset (CSV Format)**  
```csv
CVE_ID,CWE_ID,CVSS_Score,Exploitability_Score,Impact_Score,Exploit_Available,Description
CVE-2024-1001,CWE-79,7.5,8.5,6.5,1,"Cross-site scripting vulnerability in XYZ software."
CVE-2024-1002,CWE-89,9.0,9.5,8.0,1,"SQL injection vulnerability in ABC web application."
CVE-2024-1003,CWE-125,,7.0,6.0,0,"Heap buffer overflow in XYZ service."
```
🔹 **Điểm CVSS bị thiếu (`NaN`) sẽ được dự đoán.**  
🔹 **Các mô tả sẽ được xử lý bằng NLP để trích xuất các đặc trưng.**  

---

### **2️⃣ Step 2: Feature Engineering**  
We extract meaningful features from both structured and unstructured data.

#### **(a) Đặc trưng dựa trên văn bản (NLP)**
- Cột `Description` chứa dữ liệu văn bản mô tả lỗ hổng.
- Chúng ta sẽ chuyển đổi nó thành **vector số** bằng cách sử dụng **TF-IDF** hoặc **BERT embeddings**.
- Ví dụ sử dụng `sentence-transformers`:
```python
from sentence_transformers import SentenceTransformer

# Load a pre-trained NLP model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Convert descriptions to vector embeddings
df["text_embedding"] = df["Description"].apply(lambda x: model.encode(x))
```
- **Output**: Mỗi mô tả được chuyển đổi thành một **vector 384 chiều**.

#### **(b) Feature có cấu trúc**

Ở đây chúng ta cần define ra định dạng output của mô hình, kết quả mà từ đó mang lại giá trị cho người dùng về khả năng dự đoán và score, cụ thể là các đặc trưng sau:

- **CWE_ID (Mã hóa one-hot)** → Đại diện cho loại tấn công.
- **Exploit_Available (Cờ nhị phân)** → `1` nếu tồn tại khai thác, ngược lại `0`.
- **Exploitability Score & Impact Score** → Các giá trị số được trích xuất từ NVD.

**Ma trận đặc trưng cuối cùng:**
| Đặc trưng | Loại | Ví dụ |
|-----------|------|-------|
| CVE_ID | Phân loại | CVE-2024-1001 |
| CWE_ID | Mã hóa one-hot | [0,1,0,0,0,0] |
| Exploit_Available | Nhị phân | 1 |
| Exploitability_Score | Số | 8.5 |
| Impact_Score | Số | 6.5 |
| Description (BERT Embedding) | Vector | [0.23, -0.12, ..., 0.87] |

---

### **3️⃣ Step 3: Model Selection & Training**  
We train a **regression model** to predict CVSS scores.  


#### **Training the Model**
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

# Load dataset
df = pd.read_csv("cve_dataset.csv")

# Combine structured features and text embeddings
X_structured = df[["Exploit_Available", "Exploitability_Score", "Impact_Score"]].values
X_text = np.vstack(df["text_embedding"].values)  # Convert list to numpy array
X = np.hstack((X_text, X_structured))  # Concatenate text and structured data

# Target variable (CVSS Score)
y = df["CVSS_Score"].values

# Remove missing values
mask = ~np.isnan(y)
X, y = X[mask], y[mask]

# Split into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a regression model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
print(f"Mean Absolute Error: {mean_absolute_error(y_test, y_pred)}")

# Save model
joblib.dump(model, "cvss_predictor.joblib")
```

---

### **4️⃣ Bước 4: Triển khai mô hình**
Sau khi huấn luyện, chúng ta sẽ tạo một **API endpoint** để dự đoán CVSS theo thời gian thực.

#### **Endpoint FastAPI**
```python
from fastapi import FastAPI
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer

app = FastAPI()

# Load the trained model
model = joblib.load("cvss_predictor.joblib")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@app.post("/predict_cvss")
async def predict_cvss(description: str, exploit_available: int, impact_score: float, exploitability_score: float):
    # Convert text description to embedding
    text_embedding = embedder.encode(description).reshape(1, -1)
    
    # Prepare structured data
    structured_features = np.array([[exploit_available, impact_score, exploitability_score]])
    
    # Combine all features
    features = np.hstack((text_embedding, structured_features))
    
    # Predict CVSS Score
    predicted_score = model.predict(features)[0]
    
    return {"predicted_cvss": predicted_score}
```
💡 **Bây giờ, khách hàng có thể gửi mô tả lỗ hổng và dữ liệu có cấu trúc để nhận dự đoán CVSS theo thời gian thực!**


---

### Giải thích mô hình
Để hiểu **tại sao mô hình đưa ra các dự đoán nhất định**, chúng ta sử dụng **phân tích SHAP**.

**Key Insights from SHAP**

- Nếu "Exploit_Available" là 1 (Có), nó sẽ tăng điểm CVSS.
- Nếu "Impact_Score" thấp, điểm CVSS cuối cùng sẽ giảm.
- Một số danh mục CWE có thể ảnh hưởng đến mức độ nghiêm trọng khác nhau.


**SHAP giải thích lý do tại sao mô hình ML đưa ra dự đoán.**
🔹 Giúp các nhà phân tích an ninh mạng tin tưởng vào các điểm CVSS do AI dự đoán.
🔹 Có thể được sử dụng để cải thiện tính công bằng và độ chính xác của mô hình.

```python
import shap

explainer = shap.Explainer(model)
shap_values = explainer(X_test)

shap.summary_plot(shap_values, X_test)
```

Điều này giúp các chuyên gia an ninh mạng tin tưởng vào các điểm CVSS do AI tạo ra.

---

### **🚀 Tóm tắt**
✅ **Bước 1: Thu thập dữ liệu** → NVD, CWE, ExploitDB, Feedly  
✅ **Bước 2: Kỹ thuật đặc trưng** → NLP + Dữ liệu có cấu trúc  
✅ **Bước 3: Huấn luyện mô hình ML** → RandomForest, XGBoost  
✅ **Bước 4: Triển khai API** → FastAPI cho dự đoán thời gian thực  
✅ **Bước 5: Giải thích** → Phân tích SHAP  

---

### Các bước tiếp theo
- Cải thiện **tăng cường dữ liệu** bằng cách sử dụng **báo cáo tình báo mối đe dọa**.  
- Huấn luyện các **mô hình học sâu** (BERT, GPT-4) để có các biểu diễn phong phú hơn.  
- Tinh chỉnh **các mô hình tập hợp** để đạt độ chính xác cao hơn.  
