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

import React from "react";
import "typeface-roboto";
import { parseCityIO, ODarcsForThisTract } from "./components";
import "./App.css";
//get dummy OD from init
import logo from "./logo.png";
import DeckGL, {
  TextLayer,
  GeoJsonLayer,
  ArcLayer,
  FlyToInterpolator
} from "deck.gl";
import { StaticMap } from "react-map-gl";
//fixes CSS missing issue
import "mapbox-gl/dist/mapbox-gl.css";

//https://github.com/reactjs/react-timer-mixin
//https://github.com/reactjs/react-timer-mixin/issues/4
var ReactInterval = require("react-timer-mixin");
const cityIOapi = "https://cityio.media.mit.edu/api/table/CityScopeJS";
const ODapi = "https://cityio.media.mit.edu/choiceModels/volpe/v1.0/od";
const ODapiTS = "https://cityio.media.mit.edu/choiceModels/volpe/v1.0/ts";
const GeoJsonAPI = "https://cityio.media.mit.edu/choiceModels/volpe/v1.0/geo";
const INITIAL_VIEW_STATE = {
  latitude: 42.3601,
  longitude: -71.0942,
  zoom: 10,
  bearing: 0,
  pitch: 45
};
const LIGHT_SETTINGS = {
  lightsPosition: [-71.5, 41.5, 8000, -70.5, 43, 8000],
  ambientRatio: 0.4,
  diffuseRatio: 0.6,
  specularRatio: 0.8,
  lightsStrength: [0.8, 0.5, 0.8, 0.5],
  numberOfLights: 2
};

//store a dummy OD from API in global var for start
var OD = null;

// DeckGL react component
class App extends React.Component {
  constructor(props) {
    super(props);
    this.rotationStep = 0;
    this.state = {
      colors: {
        walk: [0, 225, 51],
        bike: [43, 209, 252],
        car: [255, 0, 217],
        transit: [227, 123, 64]
      },
      mode: [],
      sliderVal: 50,
      rotationStep: 0,
      thisTract: "",
      arcs: null,
      arcsArr: [],
      textArr: [],
      viewState: INITIAL_VIEW_STATE,
      cityIOtableData: null,
      GeoJsonData: null,
      slider: { type: 0, value: 0 },
      oldSlider: { type: 0, value: 0 },
      timeInterval: 1000,
      timer: null,
      oldODtimeStamp: "0"
    };
  }

  /////////////////////////

  componentDidMount() {
    console.log("INIT: getting GEO, initial OD");
    this.getGEOJSON();
    //get initial cityIO
    this.getCityIO();
    //and set interval for getting APIs
    setInterval(this.getCityIO, 1000);
  }

  // //start demo mode
  // //https://www.npmjs.com/package/react-interval
  // // https://codepen.io/nkbt/pen/ZGmpoO/
  // this.timer = ReactInterval.setInterval(() => {
  //   this._demoMode();
  // }, this.state.timeInterval)

  /////////////////////////

  getGEOJSON = async () => {
    console.log("Trying to get Geo Data");
    try {
      const res = await fetch(GeoJsonAPI);
      const d = await res.json().then(console.log("got GEO"));
      this.setState({ GeoJsonData: d });
    } catch (e) {
      console.log("ERROR for GEO:", e);
    }
  };

  /////////////////////////

  getCityIO = async () => {
    try {
      const res = await fetch(cityIOapi);
      const cityIOdata = await res.json();

      this.setState({ cityIOtableData: cityIOdata });
      const c = this.state.cityIOtableData;

      //WIP check for cityIO changes
      //get ods at the same step
      this.getOD();

      //get the slider value
      this.setState({ slider: this._sliderListener(c) });
      //check if there is a change to slider so
      //we'll fly to Volpe  tract
      this._checkNewSliderState(this.state.slider);

      //parse cityIO grid and set as state
      this.setState({ textArr: parseCityIO(c) });
    } catch (e) {
      console.log("ERROR for cityIO:", e);
    }
  };

  _checkNewSliderState = slider => {
    if (JSON.stringify(slider) !== JSON.stringify(this.state.oldSlider)) {
      this.setState({ oldSlider: this.state.slider });
      //don't demo if OD is empty
      if (OD !== null) {
        this._demoMode("volpe");
      }
    }
  };

  /////////////////////////

  //listen to slider events in cityIO
  _sliderListener = c => {
    let sliderState;
    let sliderObj = c.objects.sliders[0];
    for (
      let i = sliderObj[0];
      i <= sliderObj[1];
      i = i + c.header.spatial.ncols
    ) {
      if (c.grid[i] !== -1) {
        sliderState = {
          type: c.grid[i],
          value: i
        };
      }
    }
    return sliderState;
  };

  /////////////////////////

  getOD = async () => {
    console.log("getting OD timestamp");
    //check for new OD data
    const ts = await fetch(ODapiTS);
    const tsJSON = await ts.json();

    if (JSON.stringify(tsJSON) !== JSON.stringify(this.state.oldODtimeStamp)) {
      this.setState({ oldODtimeStamp: tsJSON });
      try {
        console.log("New TimeStamp, Trying to get OD Data");
        const res = await fetch(ODapi);
        const ODdata = await res.json();
        OD = ODdata;
        console.log("got OD data");
        return OD;
      } catch (e) {
        console.log("ERROR for OD data:", e);
      }
    } else {
      console.log("No new OD timestamp, not fetching");
    }
  };

  /////////////////////////

  _onViewStateChange = ({ viewState }) => {
    this.setState({ viewState });
  };

  _demoMode = cityIOtract => {
    if (cityIOtract === "volpe") {
      //call the fly method
      this._flyToTractCentroid(
        this.state.GeoJsonData.features[cityIOtract].properties.centroid,
        45,
        13
      );
      //an obj for arcs method
      let arcsObj = {
        object: this.state.GeoJsonData.features[cityIOtract],
        index: cityIOtract
      };
      this._arcsForSelectedTract(arcsObj);

      //if no update to slider, keep demo
    } else {
      let tractLen = this.state.GeoJsonData.features.length;
      //get random tract for display
      let rndTract = Math.floor(this._rndLoc(0, tractLen));

      if (cityIOtract > 10) {
        console.log(ReactInterval);
        ReactInterval.clearInterval(this.timer);
      }

      //call the fly method
      this._flyToTractCentroid(
        this.state.GeoJsonData.features[rndTract].properties.centroid,
        this._rndLoc(0, 90),
        this._rndLoc(10, 14)
      );
      //an obj for arcs method
      let arcsObj = {
        object: this.state.GeoJsonData.features[rndTract],
        index: rndTract
      };
      this._arcsForSelectedTract(arcsObj);
    }
  };
  //get random in range
  _rndLoc = (min, max) => {
    return Math.random() * (max - min) + min;
  };

  /////////////////////////

  _flyToTractCentroid = (centroid, bearing, zoom) => {
    this.setState({
      viewState: {
        ...this.state.viewState,
        longitude: centroid[0],
        latitude: centroid[1],
        zoom: zoom,
        pitch: 45,
        bearing: bearing,
        transitionDuration: Math.floor(this.state.timeInterval / 10),
        transitionInterpolator: new FlyToInterpolator()
      }
    });
  };

  /////////////////////////

  _arcsForSelectedTract({ object, index }) {
    this.setState({
      thisTract: { index, object }
    });
    //dont show if not on tract
    if (index < 1) {
      return;
    } else {
      const tract = this.state.thisTract.index;
      //check we already got API data
      if (OD && this.state.GeoJsonData) {
        const tractArcs = ODarcsForThisTract(tract, this.state.GeoJsonData, OD);
        this.setState({ arcsArr: tractArcs });
      }
    }
    this._modeCounter();
  }
  //helper to set the arcs width based on trips count
  _strkWidth(d) {
    let stw = d.P / 25;
    return stw;
  }

  /////////////////////////

  _Layers() {
    let allLayers = [
      new ArcLayer({
        id: "ODarc",
        data: this.state.arcsArr,
        getSourcePosition: d => d.source,
        getTargetPosition: d => d.target,
        getSourceColor: d => {
          //different mode choices
          switch (d.M) {
            //walk
            case 0:
              return this.state.colors.car;
            //bike
            case 1:
              return this.state.colors.bike;
            //car
            case 2:
              return this.state.colors.walk;
            //transit
            case 3:
              return this.state.colors.transit;
            default:
              return [255, 255, 255, 30];
          }
        },

        getTargetColor: d => [255, 255, 255, 150],
        getStrokeWidth: d => {
          return this._strkWidth(d);
        },
        transitions: {
          getSourcePosition: this.state.timeInterval / 10
        }
      }),
      new GeoJsonLayer({
        id: "TRACTS",
        data: this.state.GeoJsonData,
        extruded: false,
        wireframe: true,
        stroked: true,
        filled: true,
        pickable: true,
        onHover: d => {
          this._arcsForSelectedTract(d);
        },
        lineWidthMinPixels: 0.5,
        opacity: 0.5,
        getLineColor: d => [255, 255, 255],
        getFillColor: d => [255, 255, 255, 30],
        lightSettings: LIGHT_SETTINGS
      }),
      //
      new TextLayer({
        id: "text-layer",
        data: this.state.textArr,
        pickable: true,
        getPosition: d => d.coordinates,
        getText: d => d.cellData,
        getSize: 20,
        getColor: d => {
          switch (d.cellData) {
            case "0":
              return this.state.colors.walk;
            case "1":
              return this.state.colors.bike;
            case "2":
              return this.state.colors.car;
            case "3":
              return this.state.colors.transit;
            default:
              return [255, 255, 255];
          }
        },
        getAngle: 0,
        getTextAnchor: "middle",
        getAlignmentBaseline: "center"
      })
    ];
    return allLayers;
  }

  /////////////////////////
  //counts the different mode choices

  _modeCounter = () => {
    const thisArcsArr = this.state.arcsArr;
    let modeArr = [0, 0, 0, 0];
    for (let i = 0; i < thisArcsArr.length; i++) {
      switch (thisArcsArr[i].M) {
        //walk
        case 0:
          modeArr[0] += thisArcsArr[i].P;
          break;
        //bike
        case 1:
          modeArr[1] += thisArcsArr[i].P;
          break;
        //car
        case 2:
          modeArr[2] += thisArcsArr[i].P;
          break;
        //transit
        case 3:
          modeArr[3] += thisArcsArr[i].P;
          break;

        //
        default:
          break;
      }
    }
    this.setState({ mode: modeArr });
  };

  /////////////////////////
  _tractInfoDiv = () => {
    const thisTractIndex = this.state.thisTract.index;
    if (thisTractIndex && thisTractIndex !== -1) {
      return (
        <span className="data">
          <ul>
            <h3>Cencus Tract #{this.state.thisTract.index}</h3>
            <li>
              <span style={{ color: "rgb(" + this.state.colors.car + ")" }}>
                <span role="img" aria-label="">
                  🚗 Driving {Math.floor(this.state.mode[0])}
                </span>
              </span>
            </li>

            <li>
              <span style={{ color: "rgb(" + this.state.colors.bike + ")" }}>
                <span role="img" aria-label="">
                  🚴 Cycling {Math.floor(this.state.mode[1])}
                </span>
              </span>
            </li>

            <li>
              <span style={{ color: "rgb(" + this.state.colors.walk + ")" }}>
                <span role="img" aria-label="">
                  🚶 Walking {Math.floor(this.state.mode[2])}
                </span>
              </span>
            </li>

            <li>
              <span style={{ color: "rgb(" + this.state.colors.transit + ")" }}>
                <span role="img" aria-label="">
                  🚌 Transit {Math.floor(this.state.mode[3])}
                </span>
              </span>
            </li>
          </ul>
        </span>
      );
    }
    return null;
  };

  /////////////////////////

  render() {
    return (
      <div>
        <div className="info">
          <div className="logo">
            <img src={logo} style={{ width: 50, height: 50 }} alt="Logo" />
          </div>
          <h3>MIT CityScope</h3>
          <h1>Choice Models</h1>
          'ModCho' [short for Mobility Choices] aims to predicts mobility
          choices of simulated individuals based on thier characteristics and
          land use. ModCho's are calibrated based on census data and the
          individual choices are influenced by initial conditions, such as
          income, location or age. Than, a CityScope TUI interaction captured
          can triger new predictions based on land-use, density or proximity.
        </div>

        <this._tractInfoDiv thisTractIndex={true} />

        <DeckGL
          layers={this._Layers()}
          viewState={this.state.viewState}
          initialViewState={INITIAL_VIEW_STATE}
          onViewStateChange={this._onViewStateChange}
          controller={true}
          width="100%"
          height="100%"
        >
          <StaticMap
            mapStyle="mapbox://styles/relnox/cjl58dpkq2jjp2rmzyrdvfsds"
            mapboxApiAccessToken={
              "pk.eyJ1IjoicmVsbm94IiwiYSI6ImNpa2VhdzN2bzAwM2t0b2x5bmZ0czF6MzgifQ.KtqxBH_3rkMaHCn_Pm3Pag"
            }
          />
        </DeckGL>
      </div>
    );
  }
}

export default App;
