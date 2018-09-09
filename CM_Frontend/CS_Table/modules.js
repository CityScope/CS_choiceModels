/**
 * get cityIO method [uses polyfill]
 * @param cityIOtableURL cityIO API endpoint URL
 */

async function getCityIO(cityIOtableURL) {
  // console.log("trying to fetch " + cityIOtableURL);
  return fetch(cityIOtableURL)
    .then(function(response) {
      return response.json();
    })
    .then(function(cityIOdata) {
      // console.log("got cityIO table at " + cityIOdata.meta.timestamp);
      return cityIOdata;
    });
}

/**
 * make the initial D3 grid
 * http://blockbuilder.org/eesur/b6f66a98e398c0df28e6
 */
function makeGrid() {}
