import os
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row


app = FastAPI()

# Allow our local frontend to read backend responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://chrispy6.github.io",
    ],
    allow_methods=["GET"],
)




@app.get("/alive")
def health():
    return {"status": "ok", "application": "Rent Watcher"}


@app.get("/listings")
def get_listings(
    min_rent: Annotated[
        float | None,
        Query(ge=0, allow_inf_nan=False),
    ] = None,
    max_rent: Annotated[
        float | None,
        Query(ge=0, allow_inf_nan=False),
    ] = None,
):
    # Validate the relationship between the two optional bounds.
    if (
        min_rent is not None
        and max_rent is not None
        and min_rent > max_rent
    ):
        raise HTTPException(
            status_code=400,
            detail="Minimum rent cannot exceed maximum rent.",
        )

    # Read the password setting and connect to PostgreSQL.
    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row,
        connect_timeout=15,
    ) as connection:

        with connection.cursor() as cursor:
            # Preserve the field names expected by the frontend.
            cursor.execute(
                """
                SELECT
                    id,
                    formatted_address AS "formattedAddress",
                    city,
                    state,
                    price,
                    bedrooms,
                    bathrooms,
                    square_footage AS "squareFootage"
                FROM listings
                WHERE (%s::numeric IS NULL OR price >= %s)
                  AND (%s::numeric IS NULL OR price <= %s)
                ORDER BY price, id;
                """,
                (min_rent, min_rent, max_rent, max_rent),
            )

            listings = cursor.fetchall()

    return listings