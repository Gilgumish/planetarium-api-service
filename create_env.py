import os

env_variables = {
    "POSTGRES_DB_STATUS": "True",  # or "False"
    "POSTGRES_PASSWORD": "planetarium",
    "POSTGRES_USER": "planetarium",
    "POSTGRES_DB": "planetarium",
    "POSTGRES_HOST": "db",
    "POSTGRES_PORT": "5432",
    "PGDATA": "/var/lib/postgresql/data",
    "SECRET_KEY": "your_secret_key"
}

env_file_path = os.path.join(os.path.dirname(__file__), '.env')

with open(env_file_path, 'w') as env_file:
    for key, value in env_variables.items():
        env_file.write(f"{key}={value}\n")
