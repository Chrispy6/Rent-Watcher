# UPDATER, not an API route: a local command or GitHub Actions runs this script.
# It reserves budget, fetches RentCast data, and saves a validated pending response.
# It does not update the listings table or publish the public snapshot itself.
import os

import psycopg

import requests

import json
from pathlib import Path

# Either commit one request reservation or raise an error before any HTTP request.
# All updater runs share this persistent table, including runs on different computers.
def reserve_request():
    with psycopg.connect(
        os.environ["DATABASE_URL"],
        connect_timeout=15,
    ) as connection:
        with connection.cursor() as cursor:
            # Hold a table lock until this transaction ends. A competing updater waits,
            # then sees the committed reservation before checking its own allowance.
            cursor.execute(
                "LOCK TABLE rentcast_request_attempts IN EXCLUSIVE MODE"
            )

            # This is a rolling 35-day window, not a calendar-month counter.
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM rentcast_request_attempts
                WHERE attempted_at >= NOW() - INTERVAL '35 days';
                """
            )

            # COUNT returns one row containing one value; [0] extracts that value.
            attempts = cursor.fetchone()[0]

            # raise stops execution and rolls back this transaction; no request follows.
            if attempts >= 40:
                raise RuntimeError(
                    "RentCast request budget exhausted. No request sent."
                )

            # The database supplies the generated ID and timestamp defaults.
            cursor.execute(
                "INSERT INTO rentcast_request_attempts DEFAULT VALUES"
            )

    # A successful exit commits and closes the connection, releasing the lock.
    # Once committed, even a failed HTTP request keeps its reservation.
    # Calls made elsewhere, such as the RentCast dashboard, are not tracked here.


# Return the complete response array or raise; no automatic retry or pagination loop.
def fetch_listings():
    # Check the key before using a request reservation.
    api_key = os.environ["RENTCAST_API_KEY"].strip()

    if not api_key:
        raise RuntimeError("RENTCAST_API_KEY is empty.")

    # Commit the reservation BEFORE sending. If Neon is unavailable, execution stops here.
    reserve_request()

    # Headers carry the API key; params become URL query parameters.
    # timeout limits connection/read waits, not a strict total runtime.
    # Disabling redirects avoids following a response into an extra HTTP request.
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

    # Require the expected success response before interpreting the JSON.
    if response.status_code != 200:
        raise RuntimeError(
            f"RentCast returned HTTP {response.status_code}."
        )

    listings = response.json()

    if not isinstance(listings, list):
        raise RuntimeError("Expected a list of rental listings.")

    # A valid JSON array could still be only the first page. Compare the total
    # header with its length so a truncated dataset cannot drive stale-record deletion.
    total_count = response.headers.get("X-Total-Count")

    if total_count is None:
        raise RuntimeError("RentCast did not provide a total count.")

    if int(total_count) != len(listings):
        raise RuntimeError(
            "Response is incomplete. Stopping without updating listings."
        )

    return listings

# Check record identity and scope before saving or importing a response.
# Numeric database constraints provide further checks when the sync runs.
def validate_listings(listings):
    # Refuse to replace our data with an empty or unexpected response.
    if not isinstance(listings, list) or not listings:
        raise ValueError("Expected a nonempty list of listings.")

    # A set lets us recognize duplicate IDs while visiting each record once.
    seen_ids = set()

    for listing in listings:
        if not isinstance(listing, dict):
            raise ValueError("Each listing must be an object.")

        # .get returns None for missing keys, allowing explicit validation errors.
        listing_id = listing.get("id")
        address = listing.get("formattedAddress")

        if not isinstance(listing_id, str) or not listing_id.strip():
            raise ValueError("A listing has no valid ID.")

        if listing_id in seen_ids:
            raise ValueError(f"Duplicate listing ID: {listing_id}")

        seen_ids.add(listing_id)

        if not isinstance(address, str) or not address.strip():
            raise ValueError("A listing has no valid address.")

        # This importer is scoped to active Golden rentals, not arbitrary locations.
        if (
            listing.get("city") != "Golden"
            or listing.get("state") != "CO"
            or listing.get("status") != "Active"
        ):
            raise ValueError("Response contains an unexpected location or status.")

# Run this block only when launched directly, not when sync_pending imports validation.
if __name__ == "__main__":
    # Start from this script's location so paths do not depend on the terminal folder.
    # .parent is backend; .parent.parent is the repository root.
    project_folder = Path(__file__).resolve().parent.parent
    pending_file = project_folder / "Golden_Listings.pending.json"
    temporary_file = pending_file.with_suffix(".json.tmp")

    # This is the only direct call to the function that sends the RentCast request.
    listings = fetch_listings()
    validate_listings(listings)

    # Write a separate temporary file so an interrupted write leaves the old pending file.
    # indent=2 makes the saved JSON readable; json.dump writes Python data as JSON.
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(listings, file, indent=2)

    # Replace the pending file only after writing finishes successfully.
    temporary_file.replace(pending_file)

    print(f"Saved {len(listings)} validated listings to {pending_file.name}.")