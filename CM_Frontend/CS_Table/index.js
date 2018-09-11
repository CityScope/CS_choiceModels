/*
/////////////////////////////////////////////////////////////////////////////////////////////////////////

{{ CityScope Choice Models }}
Copyright (C) {{ 2018 }}  {{ Ariel Noyman }}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

/////////////////////////////////////////////////////////////////////////////////////////////////////////

"@context": "https://github.com/CityScope/", "@type": "Person", "address": {
"@type": "75 Amherst St, Cambridge, MA 02139", "addressLocality":
"Cambridge", "addressRegion": "MA",}, 
"jobTitle": "Research Scientist", "name": "Ariel Noyman",
"alumniOf": "MIT", "url": "http://arielnoyman.com", 
"https://www.linkedin.com/", "http://twitter.com/relno",
https://github.com/RELNO]

///////////////////////////////////////////////////////////////////////////////////////////////////////
*/
import "babel-polyfill";
//Import Storage class
import "./scripts/Storage";
var mapboxgl = require("mapbox-gl/dist/mapbox-gl.js");
import { Maptastic } from "./scripts/maptastic";
import { getCityIO, makeGrid, update } from "./scripts/modules";

async function setup() {
  //GET CITYIO
  var tableName = window.location.search.substring(1);
  if (tableName == "") {
    console.log("using default cityIO endpoint @ CityScopeJS");
    tableName = "CityScopeJS";
  }
  let cityIOtableURL =
    "https://cityio.media.mit.edu/api/table/" + tableName.toString();
  //store this url
  Storage.cityIOurl = cityIOtableURL;
  var interval = 1000;

  //call server once at start, just to init the grid
  const cityIOjson = await getCityIO(cityIOtableURL);
  // get grid size
  var gridSizeCols = cityIOjson.header.spatial.ncols;
  var gridSizeRows = cityIOjson.header.spatial.nrows;

  console.log("table size is", gridSizeCols, "x", gridSizeRows);
  // make the table div
  let tableDIV = document.createElement("div");
  tableDIV.id = "tableDIV";
  tableDIV.className = "tableDIV";
  document.body.appendChild(tableDIV);

  // make the table div
  let mapDIV = document.createElement("div");
  mapDIV.id = "mapDIV";
  mapDIV.className = "mapDIV";
  tableDIV.appendChild(mapDIV);

  //make the grid parent
  let gridDIV = document.createElement("div");
  gridDIV.className = "gridDIV";
  tableDIV.appendChild(gridDIV);

  //make the baseline grid before update kick in
  makeGrid(gridDIV, gridSizeCols, gridSizeRows);

  //maptastic the div
  Maptastic("tableDIV");

  //run the update
  window.setInterval(update, interval);

  //base map
  mapboxgl.accessToken =
    "pk.eyJ1IjoicmVsbm94IiwiYSI6ImNpa2VhdzN2bzAwM2t0b2x5bmZ0czF6MzgifQ.KtqxBH_3rkMaHCn_Pm3Pag";
  var map = new mapboxgl.Map({
    container: "mapDIV",
    style: "mapbox://styles/relnox/cjlu6w5sc1dy12rmn4kl2zljn",
    center: [-71.085202, 42.36479],
    bearing: 30,
    zoom: 17.5
  });
}

//start applet
window.onload = setup();
