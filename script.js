
//declare any variables we need to use
let listings = [];

const listing_container = document.getElementById("listing_container");
const result_count = document.getElementById("results_count");
const max_rent = document.getElementById("max_rent");
const min_rent = document.getElementById("min_rent");
const filter_button = document.getElementById("filter_button");
const reset_button = document.getElementById("reset_button");
const data_status = document.getElementById("data_status");

// Use FastAPI locally and the saved snapshot on the published demo.
const use_local_backend = ["127.0.0.1", "localhost"].includes(window.location.hostname);
const listings_url = use_local_backend
  ? "http://127.0.0.1:8000/listings"
  : "https://rent-watcher.onrender.com/listings";




async function fetchListingData(url) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Couldn't load listings: ${response.status}`);
  }

  const data = await response.json();

  if (!Array.isArray(data)) {
    throw new Error("Expected an array of listings.");
  }

  return data;
}




async function loadPublishedListings() {
  let snapshot_loaded = false;

  // Display the saved records without waiting for Render.
  try {
    listings = await fetchListingData("./Golden_Listings.json");
    snapshot_loaded = true;

    applyFilters();
    data_status.textContent =
      "Showing saved snapshot. Checking database for updates…";
  } catch (error) {
    console.error(error);
    data_status.textContent =
      "Saved snapshot unavailable. Loading database records…";
  }

  // The page remains usable while this request waits.
  try {
    listings = await fetchListingData(listings_url);

    // Reapply the current input values to the replacement data.
    applyFilters();
    data_status.textContent = "Showing database records.";
  } catch (error) {
    console.error(error);

    data_status.textContent = snapshot_loaded
      ? "Showing saved snapshot. Database service is unavailable."
      : "Unable to load listings. Please try again later.";
  }
}



function renderListings(listingsToRender) {

  //this will clear all listings so that we have a clean container to render
  listing_container.replaceChildren();

  result_count.textContent = `${listingsToRender.length} listings shown`;

  //loop through all listings and create articles to show rental listings.
  for (const listing of listingsToRender) {
    const card = document.createElement("article");
    card.className = "listing-card";

    // Use fallback text when an address is missing.
    const address = document.createElement("h2");
    address.textContent = listing.formattedAddress ?? "Address unavailable";

    const rent = document.createElement("p");
    rent.textContent = listing.price != null ? `$${listing.price.toLocaleString("en-US")} / month` : "Rent unavailable";

    const rooms = document.createElement("p");
    const bedrooms = listing.bedrooms === 0 ? "Studio" : `${listing.bedrooms ?? "Unknown"} bedrooms`;

    rooms.textContent = `${bedrooms} · ${listing.bathrooms ?? "Unknown"} bathrooms`;

    const size = document.createElement("p");
    size.textContent = listing.squareFootage > 0 ? `${listing.squareFootage.toLocaleString("en-US")} sq ft` : "Square footage unknown";

    card.append(address, rent, rooms, size);
    listing_container.append(card);

  }
}



async function applyFilters() {
  // Check the number inputs against their HTML validation rules.
  if (!min_rent.checkValidity() || !max_rent.checkValidity()) {
    result_count.textContent = "Please enter a valid dollar amount for rent.";
    return;
  }

  //here we check if there was a minimum value entered, if there was we set that value to our minimum, otherwise we just use 0
  let minimum;

  if (min_rent.value === "") {
    minimum = 0;
  } else {
    minimum = Number(min_rent.value);
  }

  //one line method of the same thing I did with minimum
  const maximum = max_rent.value === "" ? Infinity : Number(max_rent.value);


  //check if conditions are met for minimum and maximum values
  if (minimum < 0 || maximum < 0 || minimum > maximum) {
    result_count.textContent = "Rent amounts cannot be negative, and minimum cannot exceed maximum.";
    return;
  }

  if (use_local_backend) {
    // Ask PostgreSQL for matching records through FastAPI.
    await loadListings(minimum, maximum);
  } else {
    // The published demo filters its saved snapshot.
    const filtered_listings = listings.filter((listing) =>
      Number.isFinite(listing.price) &&
      listing.price >= minimum &&
      listing.price <= maximum
    );

    renderListings(filtered_listings);
  }
}




// Wait for the response data before rendering; the browser stays responsive.
async function loadListings(minimum = 0, maximum = Infinity) {
  try {
    let request_url = listings_url;

    if (use_local_backend) {
      const url = new URL(listings_url);

      url.searchParams.set("min_rent", minimum);

      if (Number.isFinite(maximum)) {
        url.searchParams.set("max_rent", maximum);
      }

      request_url = url.toString();
    }

    const response = await fetch(request_url);

    if (!response.ok) {
      throw new Error(`Couldn't load listings: ${response.status}`);
    }

    listings = await response.json();
    renderListings(listings);
  } catch (error) {
    result_count.textContent = "Cannot load listings.";
    console.error(error);
  }
}



//load all listings without any filters
if (use_local_backend) {
  loadListings();
} else {
  loadPublishedListings();
}


// Run the named handler when Apply Filter is clicked.
filter_button.addEventListener("click", applyFilters);

// Pass an inline handler that clears the filters and restores all records.
reset_button.addEventListener("click", async () => {
  min_rent.value = "";
  max_rent.value = "";

  if (use_local_backend) {
    await loadListings();
  } else {
    renderListings(listings);
  }
});



