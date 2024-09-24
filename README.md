# django-channels-examples


## Getting started
Install the necessary dependencies:
```bash
python -m venv venv
pip install -r requirements.txt
```

Migrate the database
```bash
python manage.py migrate
```

Run a channels layer:
```bash
docker run --rm -p 6379:6379 redis:7
```

Start a development server
```bash
python manage.py runserver
```