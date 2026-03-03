# wallet-api-test

This is an API for wallet service.
It's currently supports creating and making operations with wallets.
Also it has logging and tests.

## Usage

### Clone repo
```bash
git clone https://github.com/ruki-qq/wallet-api-test.git
cd wallet-api-test
```

### Running locally
Edit variables in src/core/config.py (or upload environment variables to shell) then run:
```bash
poetry install
python src/main.py
```

### Running via Docker-compose
Create .env file like .env.example in root folder then run
```bash
docker compose up
# you'll get db(PostgreSQL 16) + app containers
# all dependencies will install via pip from requirements.txt
# alembic will wait for db and then apply migrations automatically
```

After running you'll be able to create and make operations with wallets

## Testing

```bash
python -m pytest -vvv
python -m pytest --cov src # check tests coverage
```

Look available endpoints at **/docs**