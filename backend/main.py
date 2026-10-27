# API SERVER: Uvicorn imports app from this file and serves browser requests.
# os reads process environment settings; psycopg communicates with PostgreSQL.
import os
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row


# Create the application that the route decorators register endpoints on.
app = FastAPI()

# CORS lets browser pages at these origins read API responses across origins.
# An origin is scheme + hostname + port, with no /Rent-Watcher/ path.
# This browser policy is not authentication or a restriction on all API clients.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://chrispy6.github.io",
    ],
    allow_methods=["GET"],
)




# Map an HTTP GET request for /alive to the function below.
# This confirms the application responds; it does not contact the database.
@app.get("/alive")
def health():
    return {"status": "ok", "application": "Rent Watcher"}


# FastAPI reads these arguments from URL query parameters, e.g. ?min_rent=800.
# Annotated attaches Query validation to the float-or-None type. None means omitted.
# ge=0 rejects negatives; allow_inf_nan=False rejects Infinity and NaN.
# FastAPI rejects invalid individual parameters before this function runs.
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

    # Read the full connection URL from the environment rather than source code.
    # This opens a connection per request; dict_row returns rows keyed by column name.
    # The context manager closes the connection when the block finishes.
    with psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row,
        connect_timeout=15,
    ) as connection:

        # A cursor sends SQL and reads its result on this connection.
        with connection.cursor() as cursor:
            # AS aliases preserve the camelCase field names expected by JavaScript.
            # Each optional bound is used twice: once to check NULL, once to compare.
            # %s placeholders bind values separately from SQL instead of interpolating input.
            # ORDER BY makes results deterministic for records with the same rent.
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

            # Read every matching row into a list of dictionaries.
            listings = cursor.fetchall()

    # FastAPI serializes this Python data into an HTTP JSON response.
    return listings