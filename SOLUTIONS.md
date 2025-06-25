# Solution notes

### Task 01 – Run‑Length Encoder

- Language: Python, Go
- Approach: วนลูปทีละตัวอักษร แล้วนับจำนวนตัวซ้ำติดกัน จากนั้นต่อ string ออกมาเป็น '<char><count>' เช่น "AAB" จะได้ "A2B1" (Python ใช้ string, Go ใช้ rune)
- Why: เลือกวิธีนี้เพราะเข้าใจง่ายและตรงไปตรงมา (O(n)) สามารถรองรับ Unicode/emoji ได้ครบถ้วนในทุกภาษา (Go ใช้ rune, Python ใช้ str) ไม่ต้องพึ่งไลบรารีนอกและเทสต์ edge case ได้ง่าย โค้ดอ่านง่ายและ maintain ง่าย เหมาะกับโจทย์ที่ต้องการความถูกต้องและความกระชับ
- Time spent: ~15 นาที (รวมทุกภาษา)
- Edge cases: สตริงว่าง, อีโมจิ, ตัวซ้ำเกิน 10 ตัว, ตัวพิมพ์เล็ก/ใหญ่, สัญลักษณ์แปลก ๆ, combining mark
- What I'd refine: ถ้ามีเวลาเพิ่มจะลองกับ combining mark หรือ Zalgo text ให้สนุกขึ้นอีก!
- AI tools used: GitHub Copilot (ช่วย refactor และเช็ค edge case)

### Task 02 – Fix‑the‑Bug (Thread Safety)

- Language: Python, Go
- Approach: เจอ race condition ใน counter เลยใช้ lock (Python), atomic (Go) ให้การเพิ่มค่าทำแบบ atomic ป้องกันเลขซ้ำเวลาเรียกพร้อมกันหลายเธรด
- Why: ปัญหานี้เกิดจากการอ่าน-เพิ่ม-เขียน (read-increment-write) ที่ไม่ atomic ทำให้เกิด race condition เมื่อหลาย thread/process เรียกพร้อมกัน วิธีแก้ที่เลือกเป็น idiomatic ของแต่ละภาษา (Python ใช้ lock, Go ใช้ atomic) ซึ่งปลอดภัยและกระทบ performance น้อยมากในกรณีปกติ โค้ดอ่านง่ายและเข้าใจได้ทันที เหมาะกับ production จริง
- Time spent: ~10 นาที (รวมทุกภาษา)
- Edge cases: เรียกพร้อมกันเยอะ ๆ, เรียกเร็ว ๆ ติดกัน, Python GIL
- What I'd refine: ถ้าต้องใช้ข้ามเครื่องจะเปลี่ยนไปใช้ UUID หรือ distributed counter แทน
- AI tools used: GitHub Copilot (ช่วยเตือนเรื่อง atomic operation)

### Task 03 – Sync Aggregator (Concurrency & I/O)

- Language: Python, Go
- Approach: อ่านไฟล์ตามลิสต์ แล้วนับบรรทัด/คำของแต่ละไฟล์แบบขนาน (concurrent) โดยมี timeout ต่อไฟล์ และผลลัพธ์ต้องเรียงตามลำดับไฟล์ต้นฉบับ
  - Python: ใช้ multiprocessing.Process สร้าง process แยกสำหรับแต่ละไฟล์ (จำกัด workers), ใช้ Queue ส่งค่ากลับ, join ด้วย timeout ถ้าเกินเวลาจะ terminate แล้วคืน status เป็น timeout, ผลลัพธ์เรียงตามลำดับไฟล์ต้นฉบับ
  - Go: ใช้ goroutine + context.WithTimeout ต่อไฟล์, ส่งผลลัพธ์กลับผ่าน channel พร้อม index เพื่อคงลำดับ, ใช้ select รอ timeout หรือผลลัพธ์จริง
- Why: โจทย์นี้เน้น concurrency และการจัดการ timeout ต่อไฟล์ ซึ่ง Go กับ Python มีข้อจำกัดต่างกันอย่างชัดเจน:
  - **Python:**
    - Python มี Global Interpreter Lock (GIL) ทำให้ thread ไม่ได้รันพร้อมกันจริง ๆ ในงาน I/O-bound ที่มี sleep หรืออ่านไฟล์เยอะ ๆ จึงต้องใช้ process แทน thread (ผ่าน multiprocessing)
    - การสร้าง process บน macOS มี overhead สูงมาก (ทั้ง memory และ context switch) เมื่อรันพร้อมกันเยอะ ๆ จะเกิด resource contention ทำให้บาง process ช้าหรือ timeout จริง แม้จะ batch แล้ว
    - การใช้ Queue เป็นวิธีเดียวที่ปลอดภัยในการส่งค่ากลับจาก process ลูก เพราะแต่ละ process แยก memory space กัน
    - ไม่สามารถใช้ ProcessPoolExecutor ได้เพราะไม่สามารถ terminate process ที่ timeout ได้จริง (future.result(timeout=...) แค่รอ ไม่ได้ kill)
    - สรุป: แม้จะ parallel แล้ว เวลารวมยังเกือบ 6 วินาที (6.13557229199796 (ที่ทำได้ เร็วมากสุดเท่านี้ค่ะ) < 6) ถ้ารันบน Linux จะเร็วขึ้น
  - **Go:**
    - Goroutine ใน Go เบามาก (lightweight thread) สร้างได้เป็นพัน ๆ ตัวโดยไม่กระทบ performance
    - ใช้ context.WithTimeout เพื่อควบคุม timeout ต่อไฟล์ได้อย่างแม่นยำ และ select เพื่อรอผลลัพธ์หรือ timeout
    - ส่งผลลัพธ์กลับผ่าน channel พร้อม index เพื่อคงลำดับ
    - ประสิทธิภาพสูงมาก context switch เร็ว ไม่มี GIL ไม่มี process overhead เหมือน Python
    - สรุป: Go เหมาะกับงาน concurrent I/O แบบนี้มากกว่า Python อย่างเห็นได้ชัด
- Time spent: ~40 นาที (Python), ~20 นาที (Go)
- Edge cases: ไฟล์ว่าง, ไฟล์ที่มี #sleep, ไฟล์ที่ไม่มี, ไฟล์ที่อ่านไม่ได้, ไฟล์ที่ timeout
- What I'd refine: Python ถ้าอยากเร็วขึ้นอีกอาจต้องใช้ low-level pool หรือ third-party (เช่น joblib, loky) หรือ native extension, Go อาจเพิ่ม worker pool จริง ๆ (ตอนนี้ goroutine ไม่จำกัด workers)
- AI tools used: GitHub Copilot (ช่วย refactor และอธิบายข้อจำกัดของ Python)
- Note: Python บน macOS มี process overhead สูงมาก แม้จะ batch แล้ว เวลารวมยังเกือบ 6 วินาที (test กำหนด <6s) ถ้ารันบน Linux จะเร็วขึ้น

### Task 04 – SQL Reasoning (Data Analytics & Index Design)

- Language: Python
- Approach: เขียน SQL analytic query สองข้อ
  - A: รวมยอดเงินบริจาคต่อ campaign, คำนวณอัตราส่วนเทียบ target, เรียงตามเปอร์เซ็นต์มากสุด
  - B: หา percentile 90 ของยอดเงินบริจาค (global และเฉพาะ Thailand) ด้วย window function
- Why: เลือกใช้ window function และ aggregation เพราะ SQL สมัยใหม่ (เช่น SQLite/Postgres) รองรับ analytic query ได้ดี ทำให้ query กระชับ อ่านง่าย และประสิทธิภาพสูง ผลลัพธ์ตรงกับ expected output และสามารถขยายต่อยอด analytic อื่น ๆ ได้ง่าย
- Time spent: ~20 นาที (รวม debug เรื่อง scale ของเปอร์เซ็นต์)
- Edge cases: campaign ที่ไม่มี pledge, pledge ที่ donor ไม่มีประเทศ, ข้อมูลซ้ำ
- What I'd refine: ถ้ามีเวลาเพิ่มจะออกแบบ index เพิ่มเติมเพื่อเร่ง query จริง (โจทย์นี้ยังไม่ต้อง)
- AI tools used: GitHub Copilot (ช่วย format SQL และเช็ค logic)

---

> สนุกกับโจทย์นี้มากค่ะ ได้ลองคิด edge case แปลก ๆ และจินตนาการว่าถ้าเอา RLE ไปใช้กับอีโมจิหายากในพิพิธภัณฑ์ หรือ counter ไปใช้ในระบบแจกบัตรคิวคอนเสิร์ตใหญ่ ๆ หรือ aggregator ไปใช้ในระบบประมวลผลไฟล์ขนาดใหญ่ จะเป็นยังไง ถ้ามีเวลาอีกนิดจะเพิ่มลูกเล่นหรือเทสต์ขำ ๆ ให้มากขึ้นค่ะ :)
