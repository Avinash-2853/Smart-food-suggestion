#!/bin/bash
set -e

echo "⏳ Starting database seeding..."
python /app/scripts/seed_data.py

echo "⏳ Starting Qdrant vectorization..."
python /app/scripts/vector_ingestion.py

echo "✅ All database initialization complete!"
