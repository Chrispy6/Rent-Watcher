
// FRONTEND: this file runs in the browser, not in Python or on Render.
// Keep the currently loaded records here. Local API responses may already be filtered;
// the public site keeps the loaded dataset and creates filtered copies for display.
let listings = [];

// Store references to existing HTML elements so functions can update the page.
// The script tag is at the end of the body, so these elements already exist.
const listing_container = document.getElementById("listing_container");
const result_count = document.getElementById("results_count");
const max_rent = document.getElementById("max_rent");
const min_rent = document.getElementById("min_rent");
const filter_button = document.getElementById("filter_button");
const reset_button = document.getElementById("reset_button");
const data_status = document.getElementById("data_status");


// hostname excludes the port. includes() returns true for either local hostname.
// The ternary operator below chooses the local API when true, or Render when false.
// These are our own API endpoints; neither visitor path calls RentCast.
const use_local_backend = ["127.0.0.1", "localhost"].includes(window.location.hostname);
const listings_url = use_local_backend ? "http://127.0.0.1:8000/listings" : "https://rent-watcher.onrender.com/listings";




// Fetch JSON from a supplied URL and return an array of records.
// async allows await: this function pauses for data while the browser stays responsive.
// A thrown error rejects the returned Promise and is handled by the caller.
async function fetchListingData(url) {
  const response = await fetch(url);

  // fetch does not throw just because HTTP returned 404 or 500; check the status.
  if (!response.ok) {
    throw new Error(`Couldn't load listings: ${response.status}`);
  }

  // Parse the response body as JSON; this is also asynchronous.
  const data = await response.json();

  // Rendering expects an array, not an error object or another JSON shape.
  if (!Array.isArray(data)) {
    throw new Error("Expected an array of listings.");
  }

  return data;
}




// PUBLIC STARTUP: show the saved snapshot first, then request database records.
// These are separate try/catch blocks so a missing snapshot does not prevent an API try.
async function loadPublishedListings() {
  // Remember whether usable fallback data arrived before the backend request.
  let snapshot_loaded = false;

  try {
    listings = await fetchListingData("./Golden_Listings.json");
    snapshot_loaded = true;

    // On the public site, applyFilters uses the loaded array without another request.
    applyFilters();
    data_status.textContent =
      "Showing saved snapshot. Checking database for updates…";
  } catch (error) {
    console.error(error);
    data_status.textContent =
      "Saved snapshot unavailable. Loading database records…";
  }

  // The browser can handle clicks while await waits for Render to respond.
  // Records from Neon are not necessarily newer; both sources may hold the same refresh.
  try {
    listings = await fetchListingData(listings_url);

    // Reapply the current input values to the replacement data.
    applyFilters();
    data_status.textContent = "Showing database records.";
  } catch (error) {
    console.error(error);

    // Keep the snapshot records if the API fails; only the status message changes.
    data_status.textContent = snapshot_loaded
      ? "Showing saved snapshot. Database service is unavailable."
      : "Unable to load listings. Please try again later.";
  }
}



// DISPLAY ONLY: turn the supplied array into HTML cards; do not fetch or filter here.
function renderListings(listingsToRender) {

  // Remove the previous cards so repeated renders do not duplicate listings.
  listing_container.replaceChildren();

  // Count the array being displayed, which may be a filtered subset.
  result_count.textContent = `${listingsToRender.length} listings shown`;

  // Create detached DOM elements for each record, then attach them to the page.
  for (const listing of listingsToRender) {
    const card = document.createElement("article");
    // This class connects the new article to the card styles in style.css.
    card.className = "listing-card";

    // ?? uses the fallback only for null or undefined.
    // textContent displays data as text rather than interpreting it as HTML.
    const address = document.createElement("h2");
    address.textContent = listing.formattedAddress ?? "Address unavailable";

    // != null checks for both null and undefined; zero is still a value.
    // condition ? first : second chooses the rent text or its fallback.
    // toLocaleString adds US number formatting, such as 1,500.
    const rent = document.createElement("p");
    rent.textContent = listing.price != null ? `$${listing.price.toLocaleString("en-US")} / month` : "Rent unavailable";

    // Zero bedrooms means a studio, so do not treat it as missing data.
    const rooms = document.createElement("p");
    const bedrooms = listing.bedrooms === 0 ? "Studio" : `${listing.bedrooms ?? "Unknown"} bedrooms`;

    rooms.textContent = `${bedrooms} · ${listing.bathrooms ?? "Unknown"} bathrooms`;

    // Missing, zero, or negative sizes use an unknown-size label.
    const size = document.createElement("p");
    size.textContent = listing.squareFootage > 0 ? `${listing.squareFootage.toLocaleString("en-US")} sq ft` : "Square footage unknown";

    // Put the text elements inside the card, then place the card in the grid.
    card.append(address, rent, rooms, size);
    listing_container.append(card);

  }
}



// Read and validate the inputs, then choose SQL filtering locally or JS filtering publicly.
async function applyFilters() {
  // checkValidity uses the HTML input rules, such as type="number" and step.
  // The separate comparison below checks nonnegative values and the relationship.
  // return exits this function so invalid inputs do not reach the filtering step.
  if (!min_rent.checkValidity() || !max_rent.checkValidity()) {
    result_count.textContent = "Please enter a valid dollar amount for rent.";
    return;
  }

  // Input .value is a string. Empty means no lower restriction; otherwise convert to a number.
  // === compares without converting types. An empty string is different from "0".
  let minimum;

  if (min_rent.value === "") {
    minimum = 0;
  } else {
    minimum = Number(min_rent.value);
  }

  // An empty maximum uses Infinity to represent no upper bound.
  // This ternary expression is a shorter version of the if/else above.
  const maximum = max_rent.value === "" ? Infinity : Number(max_rent.value);


  // Equal bounds are allowed. Reject negative values or a reversed range.
  if (minimum < 0 || maximum < 0 || minimum > maximum) {
    result_count.textContent = "Rent amounts cannot be negative, and minimum cannot exceed maximum.";
    return;
  }

  if (use_local_backend) {
    // Ask PostgreSQL for matching records through FastAPI.
    await loadListings(minimum, maximum);
  } else {
    // Filter the currently loaded snapshot OR database response in the browser.
    // filter returns a new array and leaves listings intact, allowing Reset to restore it.
    // Each record must pass all three conditions joined with &&.
    const filtered_listings = listings.filter((listing) =>
      Number.isFinite(listing.price) &&
      listing.price >= minimum &&
      listing.price <= maximum
    );

    renderListings(filtered_listings);
  }
}




// LOCAL LOADING: request database records, optionally bounded by rent.
// Default arguments mean a zero minimum and no maximum when called with no arguments.
async function loadListings(minimum = 0, maximum = Infinity) {
  try {
    let request_url = listings_url;

    if (use_local_backend) {
      // Build query parameters safely rather than manually concatenating a URL.
      const url = new URL(listings_url);

      url.searchParams.set("min_rent", minimum);

      // Do not send Infinity: the API only accepts finite numbers.
      // Omitting max_rent tells the API to leave the upper bound unrestricted.
      if (Number.isFinite(maximum)) {
        url.searchParams.set("max_rent", maximum);
      }

      request_url = url.toString();
    }

    const response = await fetch(request_url);

    if (!response.ok) {
      throw new Error(`Couldn't load listings: ${response.status}`);
    }

    // Replace the local dataset with the response, then render it.
    listings = await response.json();
    renderListings(listings);
  } catch (error) {
    result_count.textContent = "Cannot load listings.";
    console.error(error);
  }
}



// STARTUP: local pages ask the API directly; the public page uses snapshot-first loading.
if (use_local_backend) {
  loadListings();
} else {
  loadPublishedListings();
}


// Pass the function itself (no parentheses) so the browser calls it on a future click.
filter_button.addEventListener("click", applyFilters);

// This arrow function is the click handler. Clearing .value empties the controls.
reset_button.addEventListener("click", async () => {
  min_rent.value = "";
  max_rent.value = "";

  if (use_local_backend) {
    // A local response may contain only filtered records, so request the full set again.
    await loadListings();
  } else {
    // Public filtering kept the full loaded array, so no network request is needed.
    renderListings(listings);
  }
});



