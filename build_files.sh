#!/bin/bash
# Build script for Vercel Deployment
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Applying database migrations..."
python3 manage.py migrate --noinput

echo "Seeding production baseline data..."
python3 manage.py seed_data

echo "Build completed successfully!"
