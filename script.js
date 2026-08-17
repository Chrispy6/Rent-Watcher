const listings = [
  {
    id: 1,
    title: "Downtown Denver Apartment",
    city: "Denver",
    rent: 1850,
    bedrooms: 2,
    bathrooms: 1,
    squareFeet: 900
  },
  {
    id: 2,
    title: "Lakewood Studio",
    city: "Lakewood",
    rent: 1250,
    bedrooms: 0,
    bathrooms: 1,
    squareFeet: 500
  },
  {
    id: 3,
    title: "Golden Two Bedroom",
    city: "Golden",
    rent: 2100,
    bedrooms: 2,
    bathrooms: 2,
    squareFeet: 1050
  },
  {
   id: 3,
   title: "Aurora Family Home",
   city: "Aurora",
   rent: 3000,
   bedrooms: 3,
   bathrooms: 3,
   squareFeet: 2600
  },
];

const listing_container = getElementById("listing_container");
const result_count = getElementById("results_count");
const max_rent = getElementById("max_rent");
const min_rent = getElementById("min_rent");
const filter_button = getElementById("filter_button");
const reset_button = getElementById("reset_button");