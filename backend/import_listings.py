import json
from getpass import getpass
from pathlib import Path

import psycopg


# Read the saved rental data.
project_folder = Path(__file__).resolve().parent.parent
listings_file = project_folder / "Golden_Listings.json"

with listings_file.open("r", encoding="utf-8") as file:
    listings = json.load(file)

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

with connection:

    with connection.cursor() as cursor:
        for listing in listings:
            square_footage = listing.get("squareFootage")

            # Store unknown or invalid sizes as SQL NULL.
            if square_footage is not None and square_footage <= 0:
                square_footage = None

            # Insert new records or update records with the same ID.
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

print(f"Imported or updated {len(listings)} listings.")