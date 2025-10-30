"""
Script to insert items into the SQLite database using SQLAlchemy
Run this from BACKEND directory: python insert_items.py
"""

import sys
from pathlib import Path

# Add AUTH to path so we can import the models
sys.path.insert(0, str(Path(__file__).parent / "AUTH"))

from app.utils.db import Item, SessionLocal, engine, Base

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Item data
items_data = [
    ('Samsung Galaxy A06 5G 4GB 128GB', 3490000, 'phone', 18),
    ('Chuột Gaming có dây Logitech G502X', 1699000, 'accessories', 19),
    ('iPhone 15 Pro Max 256GB', 29990000, 'phone', 17),
    ('iPhone 13 128GB', 11790000, 'phone', 12),
    ('Tai nghe choàng đầu có mic Gaming Havit H2038U', 600000, 'accessories', 15),
    ('Laptop Acer Aspire Lite 16 AL16-51P-72S2 i7 1255U/16GB/512GB/16 FHD/Win11', 15790000, 'laptop', 20),
    ('Xiaomi 15 Ultra 5G 16GB 512GB', 32990000, 'phone', 10),
    ('iPhone 15 Plus 128GB', 19590000, 'phone', 16),
    ('iPhone 14 Plus 128GB', 18490000, 'phone', 17),
    ('Samsung Galaxy A56 5G 8GB 128GB', 9490000, 'phone', 11),
    ('Macbook Air M3 13 2024 8CPU 8GPU/8GB/256GB', 24990000, 'laptop', 17),
    ('Laptop Acer Aspire 3 A315-44P-R5QG R7 5700U/16GB/512GB/15.6 FHD/Win11', 11990000, 'laptop', 10),
    ('Tai nghe gaming Remax 805 màu đen có mic', 345000, 'accessories', 0),
    ('Laptop Acer Aspire 7 A715-76-53PJ i5 12450H/16GB/512GB/15.6 FHD/Win11', 13990000, 'laptop', 20),
    ('Macbook Air 15 M4 2025 10CPU/10GPU/24GB/512GB Xanh Da Trời', 41490000, 'laptop', 20),
    ('Samsung Galaxy S24 FE 5G 128GB', 12790000, 'phone', 17),
    ('Laptop Lenovo ThinkBook 14 G7 Ultra 5 125U/AI/16GB/512GB SSD/14 WUXGA/Win11', 20990000, 'laptop', 0),
    ('Laptop Lenovo IdeaPad Slim 5 OLED 15ARP10 R7 7735HS/16GB/512GB/15.1 WQXGA/Win11', 20490000, 'laptop', 17),
    ('Bàn phím có dây Logitech K120', 180000, 'accessories', 16),
    ('Laptop MSI Gaming Thin15 B13UC-2044VN i7-13620H/16GB/512GB/15.6 FHD/RTX3050 4GB/Win11', 19190000, 'laptop', 14),
    ('iPhone 15 128GB', 15890000, 'phone', 18),
    ('Macbook Air M3 13 2024 8CPU 10GPU/16GB/256GB', 27190000, 'laptop', 11),
    ('Laptop Asus Vivobook X1404ZA-NK387W i3 1215U/8GB/512GB/14 FHD/Win11', 9890000, 'laptop', 20),
    ('Bàn phím Gaming có dây Razer Huntsman V2 Tenkeyless Linear Red Switch', 2601000, 'accessories', 10),
    ('Samsung Galaxy S25 Plus 5G 12GB 256GB', 23190000, 'phone', 14),
    ('Laptop Acer Aspire 7 Gaming A715-76G-73FM i7 12650H/16GB/512GB/15.6 FHD/RTX2050 4GB/Win11', 15990000, 'laptop', 14),
    ('Xiaomi Redmi A3 4GB 128GB', 2390000, 'phone', 12),
    ('Samsung Galaxy A06 4GB 128GB', 3190000, 'phone', 14),
    ('Xiaomi Poco M6 6GB 128GB', 3190000, 'phone', 10),
    ('Laptop HP Gaming Victus 16-s0173AX R5-7640HS/16GB/512GB/16 144Hz/RTX3050 6GB/Win11', 19890000, 'laptop', 15),
    ('Laptop Lenovo IdeaPad Slim 3 14IRH10 i5-13420H/16GB/512GB/14 WUXGA/Win11', 15490000, 'laptop', 0),
    ('Laptop Lenovo Gaming LOQ 15IAX9 i5 12450HX/12GB/512GB/15.6 FHD/RTX3050 6GB/Win11', 20490000, 'laptop', 13),
    ('Bàn phím Gaming có dây HyperX Alloy Origins Core', 1985000, 'accessories', 19),
    ('iPhone 16 Plus 128GB', 22290000, 'phone', 0),
    ('OPPO Reno12 5G 12GB 256GB', 9490000, 'phone', 14),
    ('Xiaomi Redmi Note 14 Pro Plus 5G 8GB 256GB', 10690000, 'phone', 0),
    ('Samsung Galaxy S25 5G 12GB 256GB', 19690000, 'phone', 18),
    ('Xiaomi Poco M6 Pro 8GB 256GB', 4990000, 'phone', 20),
    ('Laptop Lenovo Ideapad Slim 3 15ABR8 R5 5625U/16GB/512GB/15.6 FHD/Win11', 12490000, 'laptop', 18),
    ('Laptop Asus Vivobook E1404FA-NK186W R5 7520U/16GB/512GB/14 FHD/Win11', 11590000, 'laptop', 18),
    ('Tai nghe AirPods Pro 2022', 4990000, 'accessories', 19),
    ('Samsung Galaxy S24 Ultra 5G 256GB', 23990000, 'phone', 19),
    ('Samsung Galaxy A35 5G 128GB', 6790000, 'phone', 17),
    ('MacBook Pro 16 M4 Pro 2024 14CPU/20GPU/24GB/512GB', 64990000, 'laptop', 10),
    ('Laptop Acer Aspire Lite 14 AL14-52M-32KV i3-1305U/8GB/256GB/14 WUXGA/Win11', 9790000, 'laptop', 17),
    ('OPPO Reno12 F 5G 8GB 256GB', 7490000, 'phone', 10),
    ('Samsung Galaxy A16 5G 8GB 128GB', 5890000, 'phone', 14),
    ('Samsung Galaxy A36 5G 8GB 128GB', 7790000, 'phone', 18),
    ('iPhone 16e 128GB', 16190000, 'phone', 13),
    ('Laptop MSI Modern 15 H C13M-216VN i7-13700H/16GB/1TB/15.6 FHD/Win11', 17290000, 'laptop', 17),
    ('Tai nghe Bluetooth nhét tai Baseus Bowie E5x', 839000, 'accessories', 20),
    ('iPhone 14 128GB', 12790000, 'phone', 0),
    ('Chuột Gaming Có Dây iCore GM03', 399000, 'accessories', 19),
    ('Laptop Dell Inspiron 15 3520 i5 1235U/16GB/512GB/15.6 FHD/Win11', 16490000, 'laptop', 13),
    ('iPhone 16 128GB', 19290000, 'phone', 17),
    ('Tai nghe Bluetooth choàng đầu Gaming ICore BGH99', 890000, 'accessories', 14),
    ('Laptop Acer Aspire Lite 16 AL16-52P-572A i5 1334U/16GB/512GB/16 WUXGA/Win11', 13990000, 'laptop', 20),
    ('Samsung Galaxy A25 5G 128GB', 5790000, 'phone', 18),
    ('OPPO Find N3 Flip 5G 12GB 256GB', 16490000, 'phone', 19),
    ('Samsung Galaxy S25 Ultra 5G 12GB 256GB', 28990000, 'phone', 16),
    ('Laptop Lenovo Ideapad Slim 3 15IRH10 i5 13420H/24GB/512GB/15.3 WUXGA/Win11', 16490000, 'laptop', 0),
    ('Laptop Acer Aspire Lite 15 AL15-41P-R3U5 R7 5700U/16GB/512GB/15.6 FHD/Win11', 12990000, 'laptop', 20),
    ('Laptop Lenovo IdeaPad Slim 3 14IRH10 i5 13420H/24GB/512GB/14 WUXGA/Win11', 16490000, 'laptop', 17),
    ('Laptop Lenovo Gaming LOQ 15IAX9 i5 12450HX/16GB/512GB/15.6 FHD/RTX2050 4GB/Win11', 18990000, 'laptop', 12),
    ('Chuột Gaming không dây iCore GM08', 499000, 'accessories', 16),
    ('Laptop MSI Gaming Thin 15 B13VE-2824VN i5-13420H/16GB/512GB/15.6 FHD/RTX4050 6GB/Win11', 20990000, 'laptop', 0),
    ('Laptop MSI Gaming Thin A15 B7UC-261VN R5 7535HS/16GB/512GB/15.6 FHD/RTX3050 4GB/Win11', 17490000, 'laptop', 14),
    ('Laptop Asus TUF Gaming A15 FA506NCR-HN047W R7-7435HS/16GB/512GB/15.6 144Hz/RTX3050 4GB/Win11', 19490000, 'laptop', 11),
    ('Chuột không dây Logitech M220', 279000, 'accessories', 16),
    ('Laptop Acer Aspire Go AG15-31P-32U6 i3 N305/8GB/512GB/15.6 FHD/Win11', 8990000, 'laptop', 13),
    ('Laptop Asus Vivobook E1504FA-NJ454W R5 7520U/16GB/512GB/15.6 FHD/Win11', 11690000, 'laptop', 15),
    ('Xiaomi 14T Pro 5G 12GB 1TB', 17490000, 'phone', 13),
    ('Xiaomi 15 5G 12GB 256GB', 22990000, 'phone', 16),
    ('Xiaomi Poco M7 Pro 5G 8GB 256GB', 5690000, 'phone', 0),
    ('OPPO A3 6GB 128GB', 4590000, 'phone', 20),
    ('OPPO Find N5 5G 16GB 512GB', 44990000, 'phone', 0),
    ('Samsung Galaxy Z Fold6 5G 256GB', 37990000, 'phone', 10),
    ('iPhone 16 Pro 128GB', 25290000, 'phone', 13),
    ('Bàn phím có dây Gaming Logitech G413 TKL SE', 1470000, 'accessories', 20),
]

def insert_items():
    """Insert items into the database"""
    db = SessionLocal()
    
    try:
        # Check if items already exist
        existing_count = db.query(Item).count()
        
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} items.")
            response = input("Do you want to delete all existing items and re-insert? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                db.query(Item).delete()
                db.commit()
                print("✅ Deleted all existing items.")
            else:
                print("❌ Insertion cancelled.")
                return
        
        # Insert items
        items_to_add = []
        for device_name, price, category, in_store in items_data:
            item = Item(
                device_name=device_name,
                price=price,
                category=category,
                in_store=in_store
            )
            items_to_add.append(item)
        
        db.bulk_save_objects(items_to_add)
        db.commit()
        
        # Verify insertion
        total_items = db.query(Item).count()
        print(f"\n✅ Successfully inserted {len(items_data)} items!")
        print(f"📊 Total items in database: {total_items}")
        
        # Show sample items
        print("\n📦 Sample items:")
        sample_items = db.query(Item).limit(5).all()
        for item in sample_items:
            print(f"  - {item.device_name} ({item.category}): {item.price:,} VND (Stock: {item.in_store})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting items: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting item insertion...")
    print(f"📁 Database location: Check shared_data/auth.db or service directories")
    print()
    insert_items()

