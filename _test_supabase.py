"""Test Supabase connection and query users"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

url = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {url[:60]}...")

try:
    from sqlalchemy import create_engine, text
    engine = create_engine(url, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        # Check users
        rows = conn.execute(text("SELECT id, username, email, created_at FROM users")).fetchall()
        print(f"✅ Users in Supabase ({len(rows)} total):")
        for r in rows:
            print(f"   id={r[0]}  username={r[1]}  email={r[2]}  created={r[3]}")
        # Check sessions
        s = conn.execute(text("SELECT COUNT(*) FROM sessions")).scalar()
        print(f"✅ Sessions: {s}")
except Exception as e:
    print(f"❌ FAILED: {e.__class__.__name__}: {e}")
