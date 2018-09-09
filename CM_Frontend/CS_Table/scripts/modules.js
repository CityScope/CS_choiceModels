import "babel-polyfill";
import "./Storage";

/**
 * get cityIO method [uses polyfill]
 * @param cityIOtableURL cityIO API endpoint URL
 */
export async function getCityIO() {
  let cityIOtableURL = Storage.cityIOurl;
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
 * make the initial DIVs grid
 */
export function makeGrid(gridDIV, gridSizeCols, gridSizeRows) {
  let gridCellsArray = [];
  //cell sized in viz grid
  let cellSize = (gridDIV.clientWidth / gridSizeCols).toString() + "px";
  // make the visual rep of the now distorted grid
  for (let i = 0; i < gridSizeCols; i++) {
    var rawDIV = document.createElement("div");
    gridDIV.appendChild(rawDIV);
    rawDIV.className = "rawDIV";
    rawDIV.style.width = "100%";
    rawDIV.style.height = cellSize;
    for (let j = 0; j < gridSizeRows; j++) {
      var gridCellDIV = document.createElement("div");
      gridCellDIV.className = "gridCellDIV";
      gridCellDIV.id = (i + 1) * (j + 1);
      rawDIV.appendChild(gridCellDIV);
      gridCellDIV.style.width = cellSize;
      gridCellDIV.style.height = cellSize;

      gridCellsArray.push(gridCellDIV);
    }
  }
  Storage.gridCellsArray = gridCellsArray;
}

/**
 * controls the update sequence
 */
export async function update() {
  let cityIOtableURL = Storage.cityIOurl;
  const cityIOjson = await getCityIO(cityIOtableURL);
  renderUpdate(cityIOjson);
}

/**
 * update the DIVs grid
 * @param jsonData cityIO API endpoint data
 */

async function renderUpdate(jsonData) {
  let gridCellsArray = Storage.gridCellsArray;
  for (let i = 0; i < jsonData.grid.length; i++) {
    gridCellsArray[i].innerHTML = jsonData.grid[i].toString();

    switch (jsonData.grid[i]) {
      case -1:
        gridCellsArray[i].style.backgroundColor = "rgb(0,0,0)";
        break;
      case 0:
        gridCellsArray[i].style.backgroundColor = "rgb(50,150,255)";
        break;
      case 1:
        gridCellsArray[i].style.backgroundColor = "rgb(244,23,255)";
        break;
      default:
        gridCellsArray[i].style.backgroundColor = "gray";
    }
  }
}
