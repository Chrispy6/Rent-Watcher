# DATABASE SYNC: read the pending response and update Neon without calling RentCast.
# This script executes at the top level when launched; unlike update_listings,
# it is not designed as a module to import from other application code.
import json
import os
from pathlib import Path

import psycopg

# Importing this function does not execute update_listings' guarded startup block.
from update_listings import validate_listings


# Resolve the pending file relative to this script, not the terminal working directory.
project_folder = Path(__file__).resolve().parent.parent
pending_file = project_folder / "Golden_Listings.pending.json"

with pending_file.open("r", encoding="utf-8") as file:
    listings = json.load(file)

# Validate again: the pending file might have been changed since it was fetched.
validate_listings(listings)

# Prepare the values before making database changes.
rows = []

for listing in listings:
    square_footage = listing.get("squareFootage")

    # Python None becomes SQL NULL, representing unknown size rather than zero.
    if square_footage is not None and square_footage <= 0:
        square_footage = None

    # Each tuple follows exactly the column order in the INSERT below.
    rows.append(
        (
            listing["id"],
            listing["formattedAddress"],
            listing["city"],
            listing["state"],
            listing.get("price"),
            listing.get("bedrooms"),
            listing.get("bathrooms"),
            square_footage,
        )
    )

# Keep the complete set of current IDs for the later stale-record removal.
listing_ids = [listing["id"] for listing in listings]

# Everything inside this connection block is one transaction: all commits on success,
# or all rolls back on error. Readers do not see a partially imported dataset.
with psycopg.connect(
    os.environ["DATABASE_URL"],
    connect_timeout=15,
) as connection:
    with connection.cursor() as cursor:
        # Prevent overlapping imports from changing listings simultaneously.
        cursor.execute("LOCK TABLE listings IN EXCLUSIVE MODE")

        # Run the same parameterized INSERT for each tuple.
        # ON CONFLICT matches the primary key; EXCLUDED contains the incoming values.
        # Existing IDs update, new IDs insert, and repeated syncs do not duplicate IDs.
        cursor.executemany(
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
            rows,
        )

        # Remove only Golden, CO records whose IDs are absent from this response.
        # ANY compares an ID with the supplied PostgreSQL text array.
        # This depends on fetching a COMPLETE nonempty response first; a partial page
        # would otherwise incorrectly remove rentals that were merely on another page.
        cursor.execute(
            """
            DELETE FROM listings
            WHERE city = %s
              AND state = %s
              AND NOT (id = ANY(%s::text[]));
            """,
            ("Golden", "CO", listing_ids),
        )

        # For DELETE, rowcount reports the number of records that were removed.
        removed = cursor.rowcount

# Success here means the connection block committed all changes.
print(f"Imported or updated {len(listings)} active listings.")
print(f"Removed {removed} previously stored Golden listings.")