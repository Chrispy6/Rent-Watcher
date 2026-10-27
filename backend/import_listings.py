# INITIAL/MANUAL IMPORT: seed a database from the committed snapshot.
# Unlike sync_pending.py, this importer does not remove IDs missing from the file.
# There is no RentCast request here.
import json
from getpass import getpass
from pathlib import Path

import psycopg


# Resolve the snapshot from this file's location, then parse JSON into Python objects.
project_folder = Path(__file__).resolve().parent.parent
listings_file = project_folder / "Golden_Listings.json"

with listings_file.open("r", encoding="utf-8") as file:
    listings = json.load(file)

# getpass hides the entered credential instead of storing it in the source.
# A nonempty URL selects Neon; blank input selects the local defaults below.
database_url = getpass(
    "Neon connection string (leave blank for local database): "
).strip()

if database_url:
    connection = psycopg.connect(
        database_url,
        connect_timeout=15,
    )
else:
    password = getpass("Local PostgreSQL password: ")

    connection = psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="rent_watcher",
        user="postgres",
        password=password,
        connect_timeout=5,
    )

# Commit the whole import on success; roll it back if any statement raises an error.
# The connection closes when this block ends.
with connection:

    with connection.cursor() as cursor:
        for listing in listings:
            square_footage = listing.get("squareFootage")

            # Store unknown or invalid sizes as SQL NULL.
            if square_footage is not None and square_footage <= 0:
                square_footage = None

            # %s placeholders pass values separately from SQL.
            # ON CONFLICT uses the ID primary key; EXCLUDED holds the incoming row.
            # This makes another import update existing records instead of duplicating them.
            cursor.execute(
                """
                INSERT INTO listings (
                    id, formatted_address, city, state,
                    price, bedrooms, bathrooms, square_footage
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    formatted_address = EXCLUDED.formatted_address,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    price = EXCLUDED.price,
                    bedrooms = EXCLUDED.bedrooms,
                    bathrooms = EXCLUDED.bathrooms,
                    square_footage = EXCLUDED.square_footage;
                """,
                (
                    listing["id"],
                    listing["formattedAddress"],
                    listing.get("city"),
                    listing.get("state"),
                    listing.get("price"),
                    listing.get("bedrooms"),
                    listing.get("bathrooms"),
                    square_footage,
                ),
            )

# This count is records processed, not a count of newly inserted rows alone.
print(f"Imported or updated {len(listings)} listings.")