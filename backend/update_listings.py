import os

import psycopg

import requests

import json
from pathlib import Path

def reserve_request():
    with psycopg.connect(
        os.environ["DATABASE_URL"],
        connect_timeout=15,
    ) as connection:
        with connection.cursor() as cursor:
            # Only one updater can check and reserve at a time.
            cursor.execute(
                "LOCK TABLE rentcast_request_attempts IN EXCLUSIVE MODE"
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM rentcast_request_attempts
                WHERE attempted_at >= NOW() - INTERVAL '35 days';
                """
            )

            attempts = cursor.fetchone()[0]

            #makes sure there aren't too many api requests
            if attempts >= 40:
                raise RuntimeError(
                    "RentCast request budget exhausted. No request sent."
                )

            cursor.execute(
                "INSERT INTO rentcast_request_attempts DEFAULT VALUES"
            )

    # Leaving the connection block successfully commits the reservation.


def fetch_listings():
    # Check the key before using a request reservation.
    api_key = os.environ["RENTCAST_API_KEY"].strip()

    if not api_key:
        raise RuntimeError("RENTCAST_API_KEY is empty.")

    # This must happen before we contact RentCast.
    reserve_request()

    response = requests.get(
        "https://api.rentcast.io/v1/listings/rental/long-term",
        headers={
            "X-Api-Key": api_key,
            "Accept": "application/json",
        },
        params={
            "city": "Golden",
            "state": "CO",
            "status": "Active",
            "limit": 500,
            "includeTotalCount": "true",
        },
        timeout=30,
        allow_redirects=False,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"RentCast returned HTTP {response.status_code}."
        )

    listings = response.json()

    if not isinstance(listings, list):
        raise RuntimeError("Expected a list of rental listings.")

    total_count = response.headers.get("X-Total-Count")

    if total_count is None:
        raise RuntimeError("RentCast did not provide a total count.")

    if int(total_count) != len(listings):
        raise RuntimeError(
            "Response is incomplete. Stopping without updating listings."
        )

    return listings

def validate_listings(listings):
    # Refuse to replace our data with an empty or unexpected response.
    if not isinstance(listings, list) or not listings:
        raise ValueError("Expected a nonempty list of listings.")

    seen_ids = set()

    for listing in listings:
        if not isinstance(listing, dict):
            raise ValueError("Each listing must be an object.")

        listing_id = listing.get("id")
        address = listing.get("formattedAddress")

        if not isinstance(listing_id, str) or not listing_id.strip():
            raise ValueError("A listing has no valid ID.")

        if listing_id in seen_ids:
            raise ValueError(f"Duplicate listing ID: {listing_id}")

        seen_ids.add(listing_id)

        if not isinstance(address, str) or not address.strip():
            raise ValueError("A listing has no valid address.")

        if (
            listing.get("city") != "Golden"
            or listing.get("state") != "CO"
            or listing.get("status") != "Active"
        ):
            raise ValueError("Response contains an unexpected location or status.")

if __name__ == "__main__":
    project_folder = Path(__file__).resolve().parent.parent
    pending_file = project_folder / "Golden_Listings.pending.json"
    temporary_file = pending_file.with_suffix(".json.tmp")

    listings = fetch_listings()
    validate_listings(listings)

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(listings, file, indent=2)

    # Replace the pending file only after writing finishes successfully.
    temporary_file.replace(pending_file)

    print(f"Saved {len(listings)} validated listings to {pending_file.name}.")