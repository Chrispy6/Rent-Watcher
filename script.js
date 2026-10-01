let listings = [];

async function loadListings() {
  try {
    const response = await fetch("./Golden_Listings.json");

    if (!response.ok) {
      throw new Error(`Couldn't load listings file: ${response.status}`);
    }

    listings = await response.json();
    result_count.textContent = `${listings.length} listings loaded`;
    console.log(listings[0]);
  } catch (error) {
    result_count.textContent = "Cannot load listings.";
    console.error(error);
  }
}

const listing_container = document.getElementById("listing_container");
const result_count = document.getElementById("results_count");
const max_rent = document.getElementById("max_rent");
const min_rent = document.getElementById("min_rent");
const filter_button = document.getElementById("filter_button");
const reset_button = document.getElementById("reset_button");

loadListings();

