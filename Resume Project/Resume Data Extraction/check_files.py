import os

RESUME_DIR = r"C:\Users\User\OneDrive - Asia Pacific University\Side Project\Resume Project\Resume Dataset\pdf data"

print(f"Checking: {RESUME_DIR}")
print(f"Exists: {os.path.exists(RESUME_DIR)}")

if os.path.exists(RESUME_DIR):
    items = os.listdir(RESUME_DIR)
    print(f"Found {len(items)} items:")
    
    for item in items[:5]:  # Show first 5 items
        item_path = os.path.join(RESUME_DIR, item)
        print(f"  {item} - {'DIR' if os.path.isdir(item_path) else 'FILE'}")
        
        if os.path.isdir(item_path):
            try:
                sub_items = os.listdir(item_path)
                pdf_files = [f for f in sub_items if f.lower().endswith('.pdf')]
                print(f"    Contains {len(pdf_files)} PDF files")
                if pdf_files:
                    print(f"    Example: {pdf_files[0]}")
            except Exception as e:
                print(f"    Error reading: {e}")