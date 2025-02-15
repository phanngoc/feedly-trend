Để tạo ra một trang giúp người dùng subscribe (đăng ký) các topic quan tâm bằng **React.js + Next.js**, bạn cần thực hiện các task UI sau:

---

### **1. Thiết kế giao diện chính**
- Tạo trang `/subscribe` hoặc `/topics`
- Giao diện bao gồm:
  - **Danh sách các topic** để người dùng lựa chọn.
  - **Nút Subscribe/Unsubscribe** để đăng ký hoặc hủy đăng ký.
  - **Bộ lọc, tìm kiếm** để giúp người dùng tìm nhanh các topic quan tâm.
  - **Gợi ý topic phổ biến** hoặc **topic theo sở thích của người dùng**.

---

### **2. Hiển thị danh sách topic**
- Dữ liệu topic có thể được lấy từ API hoặc một danh sách cố định.
- Mỗi topic hiển thị:
  - **Tên topic**
  - **Mô tả ngắn**
  - **Số lượng người đã đăng ký** (nếu có)
  - **Trạng thái của người dùng (đã đăng ký hoặc chưa)**

---

### **3. Cho phép tìm kiếm và lọc topic**
- Input tìm kiếm topic theo tên.
- Bộ lọc theo danh mục, xu hướng, hoặc phổ biến nhất.

---

### **4. Xử lý hành động Subscribe/Unsubscribe**
- Khi người dùng bấm "Subscribe", cần:
  - Gửi request API cập nhật trạng thái đăng ký.
  - Cập nhật giao diện UI ngay lập tức (chuyển nút thành "Unsubscribe").
- Khi người dùng bấm "Unsubscribe", thực hiện hành động tương tự.

---

### **5. Quản lý trạng thái đăng ký của người dùng**
- Lưu danh sách topic đã đăng ký vào **state** hoặc **global state (Redux, Zustand, Context API)**
- Khi tải trang, cần fetch API để lấy danh sách topic đã đăng ký.

---

### **6. Hiển thị danh sách topic đã đăng ký**
- Có thể tạo một tab hoặc trang riêng `/my-subscriptions` để hiển thị các topic mà người dùng đã đăng ký.

---

### **7. Thông báo và phản hồi UI**
- Hiển thị **toast notification** khi người dùng đăng ký/hủy đăng ký thành công hoặc có lỗi.
- **Skeleton loading** khi dữ liệu đang tải.
- **Indicator trạng thái** (ví dụ: dấu check hoặc màu sắc thay đổi) để giúp người dùng dễ nhận biết các topic đã đăng ký.

---

### **8. Đáp ứng giao diện Mobile-Friendly**
- Thiết kế **responsive** để trang hoạt động tốt trên thiết bị di động.
- Sử dụng **bottom navigation** hoặc **dropdown menu** để quản lý danh sách topic.

---

### **9. Tối ưu SEO & Hiệu suất**
- Dùng `getServerSideProps` hoặc `getStaticProps` để fetch dữ liệu tối ưu SEO.
- Tối ưu hiệu suất bằng `useMemo` hoặc `useCallback` khi render danh sách topic.

---

Bạn có muốn một **demo code** Next.js với các tính năng trên không? 🚀