import os
import sys

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

required = {
    'ALL': ['GITHUB_TOKEN', 'GITHUB_OWNER'],
    'augment': ['AUGMENT_SESSION_AUTH'],
    'jules': ['JULES_API_KEY'],
    'openhands': ['OPENHANDS_API_KEY']
}

print("Checking environment variables...")
print()

for var in required['ALL']:
    val = os.environ.get(var)
    if val:
        print(f"✅ {var}: {val[:10]}..." if len(val) > 10 else f"✅ {var}: {val}")
    else:
        print(f"❌ {var}: NOT SET")

print()
print("Provider-specific:")
for provider, vars in required.items():
    if provider == 'ALL':
        continue
    print(f"\n{provider.upper()}:")
    for var in vars:
        val = os.environ.get(var)
        if val:
            print(f"  ✅ {var}: {val[:10]}...")
        else:
            print(f"  ⚠️  {var}: NOT SET (needed for {provider})")
