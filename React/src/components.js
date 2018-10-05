import React from "react";

import { ArcSeries, XYPlot } from "react-vis";

/////////////////////////

//make arcs from OD json
export function ODarcsForThisTract(tract, TRACTSjson, OD) {
  let tractFeatures = TRACTSjson.features;
  const arcsArr = [];
  // console.log("MAKING ARCS FOR TRACT", tract);
  let addToDestPoint = 0;

  // create the arcs array
  for (let i = 0; i < OD[tract].length; i++) {
    //count the # of arcs
    addToDestPoint++;
    if (OD[tract][i].o !== OD[tract][i].d && OD[tract][i].P > 0) {
      const firstPointInOrgTract =
        tractFeatures[OD[tract][i].o].properties.centroid;
      const firstPointInDesTract =
        tractFeatures[OD[tract][i].d].properties.centroid;

      arcsArr.push({
        source: [firstPointInOrgTract[0], firstPointInOrgTract[1]],
        target: [
          firstPointInDesTract[0] + addToDestPoint / 3000,
          firstPointInDesTract[1] + addToDestPoint / 3000
        ],
        P: OD[tract][i].P,
        M: OD[tract][i].m
      });
    }
  }
  return arcsArr;
}

/////////////////////////

export function parseCityIO(cityIOdata) {
  if (cityIOdata == null) return;
  //replace with actual loc
  const siteCord = [-71.0856854, 42.3640386];
  const textArr = [];
  let counter = 0;

  for (let i = cityIOdata.header.spatial.ncols; i > 0; i--) {
    for (let j = 0; j < cityIOdata.header.spatial.nrows; j++) {
      textArr.push({
        coordinates: [0.00025 * j + siteCord[0], 0.00025 * i + siteCord[1]],
        cellData: cityIOdata.grid[counter].toString()
      });
      counter++;
    }
  }
  return textArr;
}

/////////////////////////
// MAKE ARCS FOR ALL TRACTS
export function allODarcs(TRACTSjson, OD) {
  console.log("MAKING ALL ARCS");
  let tractFeatures = TRACTSjson.features;
  const arcsArr = [];
  //create the arcs array
  for (let i = 0; i < OD.length; i++) {
    for (let j = 0; j < OD[i].length; j++) {
      if (OD[i][j].o !== OD[i][j].d && OD[i][j].P > 1) {
        arcsArr.push({
          source: [
            tractFeatures[OD[i][j].o].geometry.coordinates[0][0][0][0],
            tractFeatures[OD[i][j].o].geometry.coordinates[0][0][0][1]
          ],
          target: [
            tractFeatures[OD[i][j].d].geometry.coordinates[0][0][0][0],
            tractFeatures[OD[i][j].d].geometry.coordinates[0][0][0][1]
          ],
          P: OD[i][j].P,
          M: OD[i][j].m
        });
      }
    }
  }

  return arcsArr;
}

//////////////////////////////////////////////
export function Chart({ data }) {
  return (
    <XYPlot width={400} height={300}>
      <ArcSeries
        data={data}
        colorDomain={[0, 1, 6]}
        colorRange={["rgb(0,200,0)", "rgb(200,0,0)", "rgb(0,0,200)"]}
        colorType="linear"
      />
    </XYPlot>
  );
}

export const data = [
  {
    angle0: 0,
    angle: Math.PI / 4,
    opacity: 0.2,
    radius: 2,
    radius0: 1,
    color: 1
  },
  {
    angle0: Math.PI / 4,
    angle: (2 * Math.PI) / 4,
    radius: 3,
    radius0: 0,
    color: 2
  },
  {
    angle0: (2 * Math.PI) / 4,
    angle: (3 * Math.PI) / 4,
    radius: 2,
    radius0: 0,
    color: 3
  },
  {
    angle0: (3 * Math.PI) / 4,
    angle: (4 * Math.PI) / 4,
    radius: 2,
    radius0: 0,
    color: 4
  },
  {
    angle0: (4 * Math.PI) / 4,
    angle: (5 * Math.PI) / 4,
    radius: 2,
    radius0: 0,
    color: 5
  }
];
