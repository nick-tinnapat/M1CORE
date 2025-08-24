# ZigZag Classic Pattern Watcher for MT5

ระบบตรวจจับแพทเทิร์นจาก ZigZag สำหรับ MetaTrader 5

## โครงสร้างระบบ

```
Core/
├── config.yml                # ไฟล์การตั้งค่าหลัก
├── run.py                    # สคริปต์เริ่มต้นการทำงาน
└── core/                     # แพ็คเกจหลัก
    ├── __init__.py
    ├── orchestrator.py       # ตัวประสานงานหลักของระบบ
    ├── config/               # โมดูลการตั้งค่า
    │   ├── __init__.py
    │   └── config.py
    ├── mt5/                  # โมดูลเชื่อมต่อ MetaTrader 5
    │   ├── __init__.py
    │   └── connection.py
    ├── zigzag/               # โมดูลคำนวณ ZigZag
    │   ├── __init__.py
    │   └── calculator.py
    ├── patterns/             # โมดูลตรวจจับแพทเทิร์น
    │   ├── __init__.py
    │   └── detector.py
    └── webhook/              # โมดูลส่งการแจ้งเตือน
        ├── __init__.py
        └── sender.py
```

## คุณสมบัติ

- อ่านพารามิเตอร์จากไฟล์ .yaml หรือ .json
- เชื่อมต่อ MetaTrader 5 พร้อมรองรับ login/password/server
- คำนวณ ZigZag แบบคลาสสิก: Depth / Deviation (points) / Backstep
- แปะป้าย HH / HL / LH / LL
- เก็บลำดับ labels ล่าสุดแบบ FIFO (สูงสุด 10)
- ตรวจจับแพทเทิร์นที่กำหนดหลายแบบ
- กันการยิงซ้ำต่อ (symbol, timeframe, pattern, last_pivot_index)
- ส่ง JSON ไปยัง Google Webhook (Apps Script / Google Chat)

## การติดตั้ง

1. ติดตั้ง Python 3.7 หรือใหม่กว่า
2. ติดตั้งแพ็คเกจที่จำเป็น:

```bash
pip install MetaTrader5 pandas requests pyyaml
```

## การใช้งาน

1. แก้ไขไฟล์ `config.yml` ตามความต้องการ
2. รันสคริปต์:

```bash
python run.py --config config.yml
```

## การทดสอบและแสดงผลด้วยภาพ

ระบบมีสคริปต์สำหรับทดสอบและแสดงผลด้วยภาพ เพื่อให้เห็นการทำงานของ ZigZag และการตรวจจับแพทเทิร์น:

1. ติดตั้ง matplotlib (หากยังไม่ได้ติดตั้ง):

```bash
pip install matplotlib
```

2. รันสคริปต์ทดสอบ:

```bash
python test.py --config config.yml
```

สคริปต์นี้จะ:
- ดึงข้อมูลกราฟจาก MT5 ย้อนหลัง 5000 แท่ง
- แสดงผลกราฟและเส้น ZigZag ด้วย matplotlib
- แสดงสัญลักษณ์ดาว (*) บนกราฟ ณ จุดที่มีการตรวจพบแพทเทิร์นและส่งสัญญาณไปยัง Webhook
- บันทึกภาพเป็นไฟล์ PNG

## การตั้งค่า

ตัวอย่างไฟล์ `config.yml`:

```yaml
mt5:
  login: 1234567
  password: "your_password"
  server: "YourBroker-Server"

symbol: "XAUUSD"
timeframe: "M5"
bars_to_fetch: 3000
poll_interval_sec: 5

zigzag:
  depth: 12
  deviation: 5
  backstep: 3

patterns:
  - ["HL", "HH", "LL", "LH", "LL"]
  - ["HH", "HL", "HH", "LH"]

webhook_url: "https://script.google.com/macros/s/REPLACE_WITH_YOUR_APPS_SCRIPT/exec"
```
