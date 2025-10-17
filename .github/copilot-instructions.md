# Operating environment

All command line executions should be run in the venv environment of conda's software environment
You can use the following command to ensure it.
   ```bash
   conda activate software
   python -m venv venv
   venv\Scripts\activate
   ```


# Rules for updating the apps

Project structure:
```
notetaking-app/
├── src/
│   ├── models/
│   │   ├── user.py          # User model (template)
│   │   └── note.py          # Note model with database schema
│   ├── routes/
│   │   ├── user.py          # User API routes (template)
│   │   └── note.py          # Note API endpoints
│   ├── static/
│   │   ├── index.html       # Frontend application
│   │   └── favicon.ico      # Application icon
│   ├── database/
│   │   └── app.db           # SQLite database file
│   └── main.py              # Flask application entry point
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

When user ask to add a feature or modify a feature, think about which part of the code should be modified.
1. Update the database if needed
2. Update the API if needed
3. Update the frontend if needed