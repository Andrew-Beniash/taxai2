#!/bin/bash
# Example script to initialize and test the tax law knowledge base

# Check if database path is provided
DB_PATH=${1:-"tax_law.db"}
echo "Using database: $DB_PATH"

# Initialize the database
echo "Initializing database..."
sqlite3 $DB_PATH < schema.sql
echo "Database initialized."

# Sample data directory - create if it doesn't exist
SAMPLE_DIR="./sample_data"
mkdir -p $SAMPLE_DIR

# Create a sample tax document for testing
echo "Creating sample document..."
cat > $SAMPLE_DIR/sample_tax_doc.txt << EOF
Internal Revenue Service Publication 523

Selling Your Home

This publication explains the tax rules that apply when you sell your main home. It explains:
- What is considered a "main home"
- How to calculate gain or loss
- How to report the sale

1. Introduction
   This publication explains sale of your main home tax rules.

1.1 Special Situations
   Some taxpayers need to review additional information.

2. Main Home
   Your main home is the one you live in most of the time.

2.1 Factors Used to Determine Main Home
   The IRS considers various factors when deciding if a home is your main residence.
EOF

echo "Loading sample document..."
python data_loader.py --source $SAMPLE_DIR/sample_tax_doc.txt --db $DB_PATH --type file

echo "Creating vector index..."
python index_manager.py --db $DB_PATH --operation create --name sample_index --type flat

echo "Searching for 'main home'..."
python index_manager.py --db $DB_PATH --operation search --name sample_index --query "What is considered a main home?" --limit 3

echo "Example complete."
