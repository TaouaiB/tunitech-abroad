# PostgreSQL and Redis Setup

## PostgreSQL

```bash
sudo -i -u postgres

# Create database and user
psql -c "CREATE DATABASE tunitech_db;"
psql -c "CREATE USER tunitech_db_user WITH PASSWORD '__PLACEHOLDER_DB_PASSWORD__';"
psql -c "ALTER ROLE tunitech_db_user SET client_encoding TO 'utf8';"
psql -c "ALTER ROLE tunitech_db_user SET default_transaction_isolation TO 'read committed';"
psql -c "ALTER ROLE tunitech_db_user SET timezone TO 'UTC';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE tunitech_db TO tunitech_db_user;"
psql -c "\c tunitech_db"
psql -d tunitech_db -c "GRANT ALL ON SCHEMA public TO tunitech_db_user;"
exit
```

## Redis
Redis should run on defaults on `127.0.0.1:6379`. Ensure it is running:
```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```
