
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
  listing_container.replaceChildren

  result_count.textContent = `${listings.length} listings shown`;

  //loop through all listings and create articles to show rental listings.
  for(const listings of listingsToRender){
    const card = document.createElelement("article");
    card.className = "listings-card";

    const adress = document.createElement("h2");
    adress.textContent = listings.formattedAdress ?? "Adress inaccessable";

    const rent = document.createElement("p");
    rent.textContent = listings.price != null;
    

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
    result_count.textContent = `${listings.length} listings loaded`;
    console.log(listings[0]);

    //catch error in case we can't load the listings itself but were able to loaod file.
  } catch (error) {
    result_count.textContent = "Cannot load listings.";
    console.error(error);
  }
}



loadListings();
renderListings();

