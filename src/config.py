import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")  # or SUPABASE_SERVICE_ROLE_KEY for admin operations

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")

# Create Supabase client with multiple fallback strategies
supabase = None

# Strategy 1: Try with minimal configuration
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client created successfully")
except Exception as e:
    print(f"✗ Failed to create Supabase client: {e}")
    
    # Strategy 2: Try with explicit empty options
    try:
        supabase = create_client(
            SUPABASE_URL, 
            SUPABASE_KEY,
            options={}
        )
        print("✓ Supabase client created with empty options")
    except Exception as e2:
        print(f"✗ Failed to create Supabase client with empty options: {e2}")
        
        # Strategy 3: Import and use basic auth
        try:
            from supabase.client import Client
            supabase = Client(SUPABASE_URL, SUPABASE_KEY)
            print("✓ Supabase client created using direct Client class")
        except Exception as e3:
            print(f"✗ Failed to create Supabase client using direct Client class: {e3}")
            raise Exception(f"All Supabase client initialization strategies failed. Original error: {e}")

if supabase is None:
    raise Exception("Failed to initialize Supabase client")