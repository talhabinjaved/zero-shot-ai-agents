import pandas as pd
from pathlib import Path

print("Testing CSV parsing...")
print()

# Test loading
try:
    df = pd.read_csv('ideas.csv')
    print(f"✅ CSV loaded: {len(df)} rows")
except Exception as e:
    print(f"❌ CSV loading failed: {e}")
    exit(1)

# Check required columns
required_cols = ['title', 'has_experiments', 'idea', 'experiments']
missing = [col for col in required_cols if col not in df.columns]

if missing:
    print(f"❌ Missing columns: {missing}")
    print(f"   Found columns: {df.columns.tolist()}")
    exit(1)
else:
    print(f"✅ All required columns present: {df.columns.tolist()}")

print()
print("Parsing rows:")
for idx, row in df.iterrows():
    title = row['title']
    has_exp_raw = row['has_experiments']
    
    # Test boolean parsing
    if isinstance(has_exp_raw, str):
        has_exp = has_exp_raw.lower() in ('true', '1', 'yes', 'y')
    else:
        has_exp = bool(has_exp_raw)
    
    exp_len = len(str(row['experiments'])) if pd.notna(row['experiments']) else 0
    
    print(f"  Row {idx}: {title[:40]:40} | has_exp={has_exp:5} | exp_len={exp_len:4}")
    
    # Validate: if has_experiments is True, experiments should not be empty
    if has_exp and exp_len == 0:
        print(f"    ⚠️  WARNING: has_experiments=True but no experiments provided")

print()
print("✅ CSV parsing test complete")
