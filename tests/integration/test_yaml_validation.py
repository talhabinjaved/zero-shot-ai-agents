import pandas as pd
import yaml

print("Testing YAML validation in pre-defined experiments...")
print()

df = pd.read_csv('ideas.csv')

for idx, row in df.iterrows():
    # Parse has_experiments
    has_exp_raw = row['has_experiments']
    if isinstance(has_exp_raw, str):
        has_exp = has_exp_raw.lower() in ('true', '1', 'yes', 'y')
    else:
        has_exp = bool(has_exp_raw)
    
    if has_exp:
        title = row['title']
        exp_yaml = row['experiments']
        
        if pd.isna(exp_yaml) or str(exp_yaml).strip() == '':
            print(f"❌ Row {idx} ({title}): has_experiments=True but experiments is empty")
            continue
        
        try:
            parsed = yaml.safe_load(str(exp_yaml))
            print(f"✅ Row {idx} ({title[:30]}): YAML valid")
            
            # Basic validation
            if 'steps' not in parsed:
                print(f"   ⚠️  WARNING: No 'steps' key in YAML")
            else:
                print(f"   Found {len(parsed['steps'])} steps")
                
        except yaml.YAMLError as e:
            print(f"❌ Row {idx} ({title}): Invalid YAML")
            print(f"   Error: {e}")

print()
print("YAML validation complete")
