Dưới đây là thiết kế database cho ứng dụng tương tự Feedly, bao gồm danh sách các bảng và cột của chúng.  

---

### **1. Bảng `users`** (Lưu thông tin người dùng)  
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **2. Bảng `feeds`** (Lưu thông tin nguồn cấp RSS)  
```sql
CREATE TABLE feeds (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    language VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **3. Bảng `articles`** (Lưu thông tin bài viết từ RSS)  
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    feed_id INT REFERENCES feeds(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    content TEXT,
    url TEXT UNIQUE NOT NULL,
    author VARCHAR(255),
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **4. Bảng `categories`** (Lưu thư mục của người dùng để quản lý nguồn)  
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **5. Bảng `subscriptions`** (Lưu đăng ký của người dùng đối với nguồn cấp dữ liệu)  
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    feed_id INT REFERENCES feeds(id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **6. Bảng `user_interactions`** (Lưu thông tin bài viết mà người dùng đã đọc hoặc lưu)  
```sql
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    article_id INT REFERENCES articles(id) ON DELETE CASCADE,
    status ENUM('unread', 'read') DEFAULT 'unread',
    is_favorite BOOLEAN DEFAULT FALSE,
    is_saved BOOLEAN DEFAULT FALSE,
    interacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **7. Bảng `notifications`** (Lưu thông báo khi có bài viết mới hoặc cập nhật)  
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **8. Bảng `settings`** (Lưu cài đặt cá nhân của người dùng)  
```sql
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    theme ENUM('light', 'dark') DEFAULT 'light',
    language VARCHAR(50) DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT TRUE
);
```

---

### **Quan hệ giữa các bảng:**  
- **`users`** có thể có nhiều **`subscriptions`** (người dùng đăng ký nhiều nguồn cấp).  
- **`feeds`** có nhiều **`articles`** (một nguồn cấp dữ liệu chứa nhiều bài viết).  
- **`users`** có thể quản lý **`categories`** để nhóm các **`subscriptions`**.  
- **`user_interactions`** lưu lại bài viết nào người dùng đã đọc, đánh dấu yêu thích hoặc lưu trữ.  
- **`notifications`** gửi cảnh báo cho người dùng về bài viết mới từ nguồn đã đăng ký.  

Với thiết kế này, ứng dụng có thể mở rộng để thêm các tính năng như tìm kiếm, API recommendation, hoặc tích hợp AI để cá nhân hóa nội dung.