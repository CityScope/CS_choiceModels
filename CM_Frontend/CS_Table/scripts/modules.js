import "babel-polyfill";
import "./Storage";

/////////////////////////////////////////////////////////////////////////////////////////////////////////
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

/////////////////////////////////////////////////////////////////////////////////////////////////////////
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
/////////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * controls the update sequence
 */
export async function update() {
  let cityIOtableURL = Storage.cityIOurl;
  const cityIOjson = await getCityIO(cityIOtableURL);
  slider(cityIOjson.grid);
  renderUpdate(cityIOjson);
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * update the DIVs grid with data from CityIO
 * @param jsonData cityIO API endpoint data
 */
async function renderUpdate(jsonData) {
  let gridCellsArray = Storage.gridCellsArray;
  for (let i = 0; i < jsonData.grid.length; i++) {
    switch (jsonData.grid[i]) {
      case 0:
        gridCellsArray[i].innerHTML = "Open";
        gridCellsArray[i].style.backgroundColor = "rgba(0,0,0,0.5)";
        break;

      case 1:
        gridCellsArray[i].style.backgroundColor = "rgba(50,150,255,0.5)";
        gridCellsArray[i].innerHTML = "Live";
        break;

      case 2:
        gridCellsArray[i].style.backgroundColor = "rgba(0, 50, 170,0.5)";
        gridCellsArray[i].innerHTML = "Live";
        break;

      case 3:
        gridCellsArray[i].style.backgroundColor = "rgba(244,0,255,0.5)";
        gridCellsArray[i].innerHTML = "Work";
        break;

      case 4:
        gridCellsArray[i].style.backgroundColor = "rgba(255,0,150,0.5)";
        gridCellsArray[i].innerHTML = "Work";
        break;
      default:
        gridCellsArray[i].style.backgroundColor = "rgba(0, 0, 0, 0)";
        gridCellsArray[i].innerHTML = "null";
        break;
    }
  }
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * looks for slider in designated grid area
 * @param jsonData cityIO API endpoint data
 */
async function slider(grid) {
  for (let i = 15; i < grid.length; i = i + 16) {
    if (grid[i] != -1 && grid[i] != 4) {
      console.log(i, grid[i]);
    }
  }
}
