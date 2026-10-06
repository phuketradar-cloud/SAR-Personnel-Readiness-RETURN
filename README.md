# SAR Personnel Readiness

เว็บแอปต้นแบบตรวจสอบความพร้อมกำลังพล ใช้ Flask + SQLite พร้อมหน้าเว็บ responsive ในตัว ไม่ต้องติดตั้ง Node.js

## ทดลองบน Windows
ติดตั้ง Python 3.11+ แล้วเปิด PowerShell ในโฟลเดอร์นี้:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="ใส่รหัสผ่านที่แข็งแรงและไม่ซ้ำ"
$env:SECRET_KEY="ใส่ค่าสุ่มยาว"
python app.py
```

เปิด http://127.0.0.1:5000 แล้วเข้าสู่ระบบด้วยบัญชีที่กำหนด หากไม่กำหนด ADMIN_PASSWORD ระบบจะสร้างรหัสผ่านชั่วคราวและแสดงใน Terminal ตอนเริ่มต้น

## อัปโหลดขึ้น GitHub
1. สร้าง repository ใหม่ (แนะนำ Private)
2. แตก ZIP แล้วอัปโหลดไฟล์ทั้งหมด หรือใช้ Git:

```bash
git init
git add .
git commit -m "Initial SAR readiness app"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

แทน USERNAME/REPOSITORY ด้วย repository ของคุณ

## Deploy ออนไลน์
GitHub เก็บ source code แต่ไม่ได้รัน Flask โดยตรง ต้องใช้ hosting ที่รองรับ Python เช่น Render:
1. Push repository ไป GitHub
2. ใน Render เลือก New → Blueprint แล้วเชื่อม repository นี้
3. ตั้ง ADMIN_USERNAME และ ADMIN_PASSWORD ที่ Render ขอ
4. ตรวจสอบ persistent disk ตาม render.yaml (แผนดังกล่าวอาจมีค่าใช้จ่าย)
5. เปิด URL ที่ Render สร้างและทดสอบล็อกอิน

## ฟังก์ชัน
- Dashboard จำนวนกำลังพล/ผู้พร้อม/ปฏิบัติงาน/ยังไม่ยืนยัน
- ค้นหาและกรองรายชื่อ
- เปลี่ยนสถานะ บันทึกหมายเหตุ และดูประวัติ
- สถานะหมดอายุหลัง 4 ชั่วโมงถูกนับเป็นยังไม่ยืนยัน
- ข้อมูลจำลอง 12 รายชื่อ

## ข้อจำกัดและความปลอดภัย
นี่คือต้นแบบ ไม่ใช่ระบบพร้อมใช้ในภารกิจจริง ก่อนใช้ข้อมูลจริงหรือเปิดเครือข่ายภายนอก ต้องได้รับอนุมัติและเพิ่ม/ตรวจสอบ CSRF protection, rate limiting, การจัดการผู้ใช้และสิทธิ์, backup/restore, audit logging และการตั้งค่า HTTPS/access policy อย่า commit รหัสผ่าน ฐานข้อมูล หรือข้อมูลกำลังพลจริงขึ้น GitHub. ระบบไม่ยืนยันตำแหน่งจริงและไม่แทนช่องทางสั่งการของหน่วยงาน.
