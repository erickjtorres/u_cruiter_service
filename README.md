# U Cruiter Services

## Requirements

- Postgres SQL
- Python 3
- pgadmin (recommended)


## Getting Started 
    1. Navigate to project directory
    2. Start a virtual environment `source [nameOfFolder]/bin/activate` (optional)
    3. $ pip3 install -r requirements.txt
    4. Start up the DB `$ brew services start postgresql or pg_ctl -D /usr/local/var/postgres start`
    5. Modify SQLALCHEMY_DATABASE_URI in db.py 'postgresql://[username]:[passsword]@localhost/[database_name]'
    6. Run the server: `python3 app.py`

## Files Included
- Models (This folder contains the models that are a 1 to 1 mapping within the database tables)
- app.py (This contains all the endpoints to the server)
- db.py (This will contain all the database configuration)


Starting DB: brew services start postgresql or pg_ctl -D /usr/local/var/postgres start
Starting server: python3 app.py