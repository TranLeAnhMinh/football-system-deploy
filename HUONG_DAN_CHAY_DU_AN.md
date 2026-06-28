# Hướng dẫn chạy dự án Football Management bằng Docker

Tài liệu này hướng dẫn cách chạy dự án Football Management sau khi đã được đóng gói bằng Docker/Docker Compose.

## 1. Yêu cầu môi trường

Máy chạy dự án cần cài sẵn:

- Docker
- Docker Compose
- Git

Kiểm tra Docker:

```bash
docker --version
docker compose version
```

Nếu hệ thống đang dùng Docker Compose bản cũ, có thể dùng:

```bash
docker-compose --version
```

## 2. Lấy mã nguồn dự án

Clone source code về máy:

```bash
git clone <https://github.com/TranLeAnhMinh/football-system-deploy.git>
cd football-system-deploy
```

Nếu source đã có sẵn trên server thì chỉ cần vào thư mục dự án:

```bash
cd ~/football-system-deploy
```

## 3. Kiểm tra file cấu hình

Trong thư mục dự án cần có các file chính như:

```text
docker-compose.yml
nginx/
spring-app/
rasa/
rasa-actions/
```

Nếu dự án sử dụng biến môi trường, cần kiểm tra file `.env` hoặc các biến được khai báo trong `docker-compose.yml`, ví dụ:

```text
SPRING_DATASOURCE_URL
SPRING_DATASOURCE_USERNAME
SPRING_DATASOURCE_PASSWORD
JWT_SECRET
VNPAY_CONFIG
```

## 4. Build và chạy toàn bộ hệ thống

Chạy lệnh sau để build image và khởi động các container:

```bash
docker compose up -d --build
```

Nếu dùng Docker Compose bản cũ:

```bash
docker-compose up -d --build
```

Sau khi chạy thành công, kiểm tra danh sách container:

```bash
docker ps
```

Các container chính của hệ thống gồm:

```text
spring-app      Backend Spring Boot
rasa            Rasa Chatbot
rasa-actions    Rasa Action Server
nginx           Reverse proxy / web server
```

## 5. Truy cập hệ thống

Nếu chạy trên server đã cấu hình domain:

```text
http://footballmanagement.id.vn/
```

Nếu chạy local:

```text
http://localhost/
```

API backend thường được truy cập qua:

```text
http://localhost/api/...
```

hoặc:

```text
http://footballmanagement.id.vn/api/...
```

## 6. Xem log container

Xem log toàn bộ hệ thống:

```bash
docker compose logs -f
```

Xem log từng container:

```bash
docker compose logs -f spring-app
docker compose logs -f rasa
docker compose logs -f rasa-actions
docker compose logs -f nginx
```

Nếu dùng bản cũ:

```bash
docker-compose logs -f spring-app
```

## 7. Khởi động lại container

Khởi động lại toàn bộ hệ thống:

```bash
docker compose restart
```

Khởi động lại một container cụ thể:

```bash
docker compose restart spring-app
```

## 8. Cập nhật code và chạy lại

Khi sửa code backend Spring Boot:

```bash
docker compose up -d --build spring-app
```

Khi sửa code Rasa Action Server:

```bash
docker compose up -d --build rasa-actions
```

Khi sửa cấu hình nginx:

```bash
docker compose up -d --build nginx
```

Lệnh này chỉ build lại container được chỉ định, các container khác không bị rebuild.

## 9. Dừng hệ thống

Dừng container nhưng không xóa:

```bash
docker compose stop
```

Dừng và xóa container:

```bash
docker compose down
```

Lưu ý: `docker compose down` sẽ stop và remove container, nhưng không xóa image và volume nếu không thêm tùy chọn khác.

Không nên chạy lệnh sau nếu không muốn mất dữ liệu volume:

```bash
docker compose down -v
```

## 10. Kiểm tra nhanh API đăng nhập

Ví dụ kiểm tra API login:

```bash
curl -X POST http://footballmanagement.id.vn/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your_email@gmail.com","password":"your_password"}'
```

Nếu thành công, hệ thống sẽ trả về:

```json
{
  "accessToken": "...",
  "refreshToken": "...",
  "userId": "...",
  "role": "USER"
}
```

## 11. Một số lỗi thường gặp

### Container không chạy

Kiểm tra log:

```bash
docker compose logs -f <container-name>
```

Ví dụ:

```bash
docker compose logs -f spring-app
```

### Cổng đã bị chiếm

Kiểm tra tiến trình đang dùng port:

```bash
sudo lsof -i :80
sudo lsof -i :8080
```

### Backend không kết nối được database

Kiểm tra lại biến môi trường database trong `docker-compose.yml` hoặc `.env`.

### Rasa không phản hồi

Kiểm tra cả hai container:

```bash
docker compose logs -f rasa
docker compose logs -f rasa-actions
```

## 12. Lệnh thường dùng

```bash
# Build và chạy toàn bộ
docker compose up -d --build

# Xem container đang chạy
docker ps

# Xem log backend
docker compose logs -f spring-app

# Restart backend
docker compose restart spring-app

# Build lại backend
docker compose up -d --build spring-app

# Dừng hệ thống
docker compose stop

# Dừng và xóa container
docker compose down
```
