# Without duplicate check

from datasets import load_dataset
import pandas as pd
import json
import sqlite3

# Specify data category 

#review_categories = ["raw_review_Electronics", "raw_review_Software"]
#metadata_categories = ["raw_meta_Electronics", "raw_meta_Software"]

review_categories = []
metadata_categories = ["raw_meta_Electronics"]



def preprocess_reviews(category, conn, batch_size=10000):
    """Preprocess and insert reviews into the database in batches."""
    dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", category, streaming=True)
    cursor = conn.cursor()

    batch = []
    for row in dataset['full']:
        try:
            # Validate and convert timestamp
            if 0 <= row['timestamp'] <= 2147483647:  # Unix timestamp range
                row['timestamp'] = pd.to_datetime(row['timestamp'], unit='s')

                # Filter for 2023 reviews
                if row['timestamp'].year == 2023:
                    batch.append((
                        row['rating'], row['title'], row['text'], row['asin'],
                        row['parent_asin'], row['timestamp'], row['helpful_vote']
                    ))

        except Exception as e:
            print(f"Skipping invalid row due to error: {e}")

        # Insert batch into the database
        if len(batch) == batch_size:
            cursor.executemany('''
                INSERT INTO reviews (rating, title, text, asin, parent_asin, timestamp, helpful_vote)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conn.commit()
            batch = []

    # Insert any remaining rows
    if batch:
        cursor.executemany('''
            INSERT INTO reviews (rating, title, text, asin, parent_asin, timestamp, helpful_vote)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()


def preprocess_metadata(category, conn, batch_size=1000):
    """Preprocess and insert metadata into the database in batches."""
    dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", category, streaming=True)
    cursor = conn.cursor()

    batch = []
    for row in dataset['full']:
        try:
            # Filter items with more than 50 ratings
            if row['rating_number'] > 50:
                # Convert JSON fields
                features = json.dumps(row['features'])
                description = json.dumps(row['description'])
                categories = json.dumps(row['categories'])
                details = json.dumps(row['details'])

                batch.append((
                    row['main_category'], row['title'], row['average_rating'], row['rating_number'],
                    features, description, row['price'], row['parent_asin'], categories, details
                ))

        except Exception as e:
            print(f"Skipping invalid metadata row due to error: {e}")

        # Insert batch into the database
        if len(batch) == batch_size:
            cursor.executemany('''
                INSERT INTO metadata (main_category, title, average_rating, rating_number, features,
                                      description, price, parent_asin, categories, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conn.commit()
            batch = []

    # Insert any remaining rows
    if batch:
        cursor.executemany('''
            INSERT INTO metadata (main_category, title, average_rating, rating_number, features,
                                  description, price, parent_asin, categories, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()


def create_tables(conn):
    """Create SQLite tables for reviews and metadata."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating REAL,
            title TEXT,
            text TEXT,
            asin TEXT,
            parent_asin TEXT,
            timestamp DATETIME,
            helpful_vote INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            asin TEXT PRIMARY KEY,
            main_category TEXT,
            title TEXT,
            average_rating REAL,
            rating_number INTEGER,
            features TEXT,
            description TEXT,
            price REAL,
            parent_asin TEXT,
            categories TEXT,
            details TEXT
        )
    ''')
    conn.commit()



def main():

    # Connect to SQLite database
    conn = sqlite3.connect('amazon_reviews_filtered.db')
    create_tables(conn)

    # Process and insert reviews in batches
    for category in review_categories:
        print(f"Processing reviews for category: {category}")
        preprocess_reviews(category, conn)

    # Process and insert metadata in batches
    for category in metadata_categories:
        print(f"Processing metadata for category: {category}")
        preprocess_metadata(category, conn)

    # Verify
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM reviews')
    print(f"Number of reviews: {cursor.fetchone()[0]}")
    cursor.execute('SELECT COUNT(*) FROM metadata')
    print(f"Number of metadata entries: {cursor.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    main()

