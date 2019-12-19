web: gunicorn base.wsgi --log-file -
worker: celery -A base worker --loglevel=info