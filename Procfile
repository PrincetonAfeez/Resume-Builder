web: gunicorn resume_builder.wsgi:application --bind 0.0.0.0:${PORT:-8000}
release: python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py createcachetable && python manage.py check_production_runtime
prune: python manage.py prune_stale_profiles
