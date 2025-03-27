import os
from dotenv import load_dotenv
from anthropic import Anthropic
import sqlite3

# Load environment variables
load_dotenv()

# Check if API key is set
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ERROR: ANTHROPIC_API_KEY not found in environment variables")
    print("Make sure you've created a .env file with your API key")
    exit(1)
else:
    print("✅ ANTHROPIC_API_KEY found")

# Try to initialize the client
try:
    client = Anthropic(api_key=api_key)
    print("✅ Successfully initialized Anthropic client")
except Exception as e:
    print(f"❌ Error initializing Anthropic client: {e}")
    exit(1)

# Test a simple API call
try:
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Hello, Claude!"}],
        max_tokens=100
    )
    print("✅ Successfully made API call to Claude")
    print(f"Response: {response.content[0].text}")
except Exception as e:
    print(f"❌ Error calling Claude API: {e}")
    exit(1)

# Test SQLite database
try:
    db_path = 'mortgage_products.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Creating a sample database...")
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Create table
        c.execute('''
        CREATE TABLE mortgage_products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            rate_type TEXT,
            min_income REAL,
            min_deposit REAL,
            interest_rate TEXT,
            comparison_rate TEXT,
            offset_account TEXT,
            redraw_facility TEXT,
            extra_repayments TEXT
        )
        ''')
        
        # Insert some sample products
        sample_products = [
            (1, "Fixed Rate Home Loan", "fixed", 60000, 0.1, "3.5%", "3.7%", "No", "No", "Yes"),
            (2, "Variable Rate Home Loan", "variable", 60000, 0.1, "3.2%", "3.4%", "Yes", "Yes", "Yes"),
            (3, "Low Rate Home Loan", "variable", 80000, 0.2, "2.9%", "3.1%", "Yes", "Yes", "Yes")
        ]
        
        c.executemany('''
        INSERT INTO mortgage_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)
        
        conn.commit()
        conn.close()
        print("✅ Created sample database with 3 mortgage products")
    else:
        # Test if we can read from the database
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM mortgage_products')
        count = c.fetchone()[0]
        conn.close()
        
        print(f"✅ Database exists with {count} mortgage products")
except Exception as e:
    print(f"❌ Error with SQLite database: {e}")
    print("You may need to run setup_database.py to initialize the database")
    exit(1)

print("\n✅ All checks passed! Your environment is correctly set up.")
print("Run your application with: streamlit run mortgage_advisor.py")