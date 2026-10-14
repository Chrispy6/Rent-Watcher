
//declare any variables we need to use
let listings = [];

const listing_container = document.getElementById("listing_container");
const result_count = document.getElementById("results_count");
const max_rent = document.getElementById("max_rent");
const min_rent = document.getElementById("min_rent");
const filter_button = document.getElementById("filter_button");
const reset_button = document.getElementById("reset_button");

function renderListings(listingsToRender) {

  //this will clear all listings so that we have a clean container to render
  listing_container.replaceChildren();

  result_count.textContent = `${listingsToRender.length} listings shown`;

  //loop through all listings and create articles to show rental listings.
  for (const listing of listingsToRender) {
    const card = document.createElement("article");
    card.className = "listing-card";

    //learned the ?? method to replace left value with the right if the left is null or undefined from W3Schools
    const address = document.createElement("h2");
    address.textContent = listing.formattedAddress ?? "Address inaccessable";
    const rent = document.createElement("p");
    rent.textContent = listing.price != null
      ? `$${listing.price.toLocaleString("en-US")} / month`
      : "Rent unavailable";

    const rooms = document.createElement("p");
    const bedrooms = listing.bedrooms === 0
      ? "Studio"
      : `${listing.bedrooms ?? "Unknown"} bedrooms`;

    rooms.textContent =
      `${bedrooms} · ${listing.bathrooms ?? "Unknown"} bathrooms`;

    const size = document.createElement("p");
    size.textContent = listing.squareFootage > 0
      ? `${listing.squareFootage.toLocaleString("en-US")} sq ft`
      : "Square footage unknown";

    card.append(address, rent, rooms, size);
    listing_container.append(card);

  }



}

//I'm using an asynchronous function here because I need to make
//sure that we wait until all listings get loaded before we do anything else 
async function loadListings() {
  try {
    //try to get the rental listings
    const response = await fetch("./Golden_Listings.json");

    //throw error in case we can't grab the listings file for any reason
    if (!response.ok) {
      throw new Error(`Couldn't load listings file: ${response.status}`);
    }

    //print out how many listings were loaded
    listings = await response.json();
    renderListings(listings);

    //catch error in case we can't load the listings itself but were able to loaod file.
  } catch (error) {
    result_count.textContent = "Cannot load listings.";
    console.error(error);
  }
}



loadListings();


