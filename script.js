
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

    //the ?? and ? : method is used to replace left value with the right based on a condition 
    const address = document.createElement("h2");
    address.textContent = listing.formattedAddress ?? "Address inaccessable";

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

function applyFilters() {
  //check if the inputted numbers are actually numbers
  if (!min_rent.checkValidity() || !max_rent.checkValidity()) {
    result_count.textContent = "please enter a valid dollar amount for rent";
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
    result_count.textContent = "minimum and maximum must be positive and minimum must be less than maximum";
    return;
  }

  //make a new array cointaining listings that fall within the rent price filters 
  const filtered_listings = listings.filter((listing) => { return Number.isFinite(listing.price) && listing.price >= minimum && listing.price <= maximum; });

  //render these new filtered listings
  renderListings(filtered_listings);

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

//load all listings without any filters
loadListings();


//waits for user to press filter button to filter listings based on inputted numbers. We pass the applyFilters function here 
filter_button.addEventListener("click", applyFilters);

//waits for user to press reset button to get rid of filters and load all listings. We dont pass a initially created function here 
// (we make a tiny one ourselves that resets the filters so that all listings are displayed)
reset_button.addEventListener("click", () => {min_rent.value = ""; max_rent.value = ""; renderListings(listings);})



