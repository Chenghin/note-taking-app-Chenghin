# Supabase Migration Summary

## What Was Changed

### 1. Configuration
- **NEW**: `src/config.py` - Supabase client configuration using environment variables
- **UPDATED**: `requirements.txt` - Added `supabase==2.3.0` and `psycopg2-binary==2.9.9`

### 2. Models Refactored
- **`src/models/user.py`**: Converted from SQLAlchemy to Supabase client
- **`src/models/note.py`**: Converted from SQLAlchemy to Supabase client

### 3. Routes Updated
- **`src/routes/user.py`**: Updated all endpoints to use new User model
- **`src/routes/note.py`**: Updated all endpoints to use new Note model

### 4. Main Application
- **`src/main.py`**: Removed SQLAlchemy configuration, added Supabase connection test

### 5. Migration & Deployment
- **NEW**: `scripts/migrate_sqlite_to_supabase.py` - Migration script for existing data
- **NEW**: `vercel.json` - Vercel deployment configuration

## Required Environment Variables

Add these to your `.env` file:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
GITHUB_TOKEN=your_github_token_for_llm
```

## Database Schema (Create in Supabase)

```sql
-- Create users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(80) UNIQUE NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create notes table
CREATE TABLE notes (
  id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  "order" INTEGER NOT NULL DEFAULT 0,
  tags TEXT, -- JSON string for tags
  event_date VARCHAR(50),
  event_time VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Add RLS policies if needed
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Add policies for public access (adjust as needed)
CREATE POLICY "Public read access" ON notes FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON notes FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access" ON notes FOR UPDATE USING (true);
CREATE POLICY "Public delete access" ON notes FOR DELETE USING (true);

CREATE POLICY "Public read access" ON users FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access" ON users FOR UPDATE USING (true);
CREATE POLICY "Public delete access" ON users FOR DELETE USING (true);
```

## Migration Steps

### Step 1: Setup Supabase
1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Run the SQL schema above in the Supabase SQL editor
4. Get your project URL and anon key from Settings > API

### Step 2: Configure Environment
```bash
# Activate your conda environment
conda activate software
python -m venv venv
venv\Scripts\activate

# Install new dependencies
pip install supabase psycopg2-binary

# Create/update .env file with Supabase credentials
```

### Step 3: Migrate Data (Optional)
If you have existing SQLite data:
```bash
python scripts/migrate_sqlite_to_supabase.py
```

### Step 4: Test Locally
```bash
python src/main.py
```

Visit `http://localhost:5001` to test the application.

### Step 5: Deploy to Vercel
1. Push code to GitHub
2. Connect repository to Vercel
3. Add environment variables in Vercel dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `GITHUB_TOKEN`
4. Deploy

## API Changes

All API endpoints remain the same - no frontend changes needed:

- `GET /api/notes` - Get all notes
- `POST /api/notes` - Create note
- `GET /api/notes/{id}` - Get specific note
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note
- `POST /api/notes/reorder` - Reorder notes
- `POST /api/notes/{id}/translate` - Translate note
- `POST /api/notes/{id}/generate-tags` - Generate tags
- `POST /api/notes/generate` - Generate note from text
- `GET /api/notes/search?q=query` - Search notes

## Key Benefits

- ✅ **Scalable**: PostgreSQL handles concurrent users
- ✅ **Cloud-native**: No file system dependencies
- ✅ **Vercel-ready**: Serverless deployment compatible
- ✅ **Real-time capable**: Supabase provides websockets
- ✅ **API consistent**: No frontend changes required

## Troubleshooting

### Connection Issues
- Verify SUPABASE_URL and SUPABASE_ANON_KEY in .env
- Check Supabase project is active and accessible
- Ensure RLS policies allow your operations

### Migration Issues
- Verify SQLite database exists at `database/app.db`
- Check Supabase tables are created correctly
- Use SERVICE_ROLE_KEY instead of ANON_KEY for migration if needed

### Deployment Issues
- Ensure all environment variables are set in Vercel
- Check that `vercel.json` is in the root directory
- Verify Python dependencies in `requirements.txt`