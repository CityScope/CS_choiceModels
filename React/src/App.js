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
  LinearInterpolator,
  FlyToInterpolator
} from "deck.gl";
import { StaticMap } from "react-map-gl";
//fixes CSS missing issue
import "mapbox-gl/dist/mapbox-gl.css";

var TimerMixin = require("react-timer-mixin");

const transitionInterpolator = new LinearInterpolator(["bearing"]);
const cityIOapi = "https://cityio.media.mit.edu/api/table/CityScopeJS";
const ODapi = "https://cityio.media.mit.edu/choiceModels/volpe/v1.0/od";
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

//store a dunmmy OD from API in global var for start
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
      GeoJsonData: null
    };
  }

  /////////////////////////

  componentDidMount() {
    this.getGEOJSON();
    //get initial cityIO
    this.getCityIO();
    //and set interval
    setInterval(this.getCityIO, 2000);
    setInterval(this.getOD, 2000);

    TimerMixin.setInterval(() => {
      this._demoMode();
    }, 5000);
  }

  /////////////////////////

  getOD = async () => {
    try {
      const res = await fetch(ODapi);
      const ODdata = await res.json();
      OD = ODdata;
      return OD;
    } catch (e) {
      console.log("err:", e);
    }
  };

  getGEOJSON = async () => {
    console.log("Trying to get Geo Data");
    try {
      const res = await fetch(GeoJsonAPI);
      const d = await res.json();
      this.setState({ GeoJsonData: d });
    } catch (e) {
      console.log("err:", e);
    }
  };

  getCityIO = async () => {
    try {
      const res = await fetch(cityIOapi);
      const cityIOdata = await res.json();
      this.setState({ cityIOtableData: cityIOdata });
      const c = this.state.cityIOtableData;
      this.setState({ textArr: parseCityIO(c) });
    } catch (e) {
      console.log(e);
    }
  };

  /////////////////////////

  _onViewStateChange = ({ viewState }) => {
    this.setState({ viewState });
  };

  /////////////////////////

  _onLoad = () => {
    this._rotateCamera();
  };
  /////////////////////////

  _demoMode = () => {
    let tractLen = this.state.GeoJsonData.features.length;
    let rndTract = Math.floor(this._rndLoc(0, tractLen));
    // this._onHoverTract(this.state.GeoJsonData.features[rndTract], rndTract);

    this._flyTo(
      this.state.GeoJsonData.features[rndTract].properties.centroid,
      this._rndLoc(0, 180)
    );
  };

  _rndLoc = (min, max) => {
    return Math.random() * (max - min) + min;
  };

  /////////////////////////

  // change bearing by 120 degrees.
  _rotateCamera = () => {
    // change bearing by 120 degrees.
    const bearing = this.state.viewState.bearing;
    this.setState({
      viewState: {
        ...this.state.viewState,
        bearing,
        transitionDuration: 100000,
        transitionInterpolator,
        onTransitionEnd: this._rotateCamera
      }
    });
  };

  /////////////////////////

  _flyTo = (centroid, bearing) => {
    this.setState({
      viewState: {
        ...this.state.viewState,
        longitude: centroid[0],
        latitude: centroid[1],
        zoom: 12,
        pitch: 45,
        bearing: bearing,
        transitionDuration: 4000,
        transitionInterpolator: new FlyToInterpolator()
      }
    });
  };

  /////////////////////////

  _onHoverTract({ object, index }) {
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

  //helper to set the line width based on trips count
  _strkWidth(d) {
    let stw = d.P * 2;
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
            case 0: //drive, cycle, walk, PT
              return this.state.colors.car;
            //bike
            case 1: //
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

        getTargetColor: d => [255, 255, 255, 50],
        getStrokeWidth: d => {
          return this._strkWidth(d);
        },
        transitions: {
          getStrokeWidth: 500,
          getSourceColor: 500
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
          this._onHoverTract(d);
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

  getInitialState = () => {
    this.setState({ sidlerValue: 50 });
  };

  /////////////////////////

  sliderChange = event => {
    this.setState({ sidlerValue: event.target.value });
  };

  /////////////////////////
  //counts the different mode choices

  _modeCounter = () => {
    const thisArr = this.state.arcsArr;
    let modeArr = [0, 0, 0, 0];
    for (let i = 0; i < thisArr.length; i++) {
      switch (thisArr[i].M) {
        //walk
        case 0:
          modeArr[0]++;
          break;
        //bike
        case 1:
          modeArr[1]++;
          break;
        //car
        case 2:
          modeArr[2]++;
          break;
        //transit
        case 3:
          modeArr[3]++;
          break;
        default:
          break;
      }
    }
    this.setState({ mode: modeArr });
  };

  _mouseOnTract = () => {
    const thisTractIndex = this.state.thisTract.index;
    if (thisTractIndex && thisTractIndex !== -1) {
      return (
        <span>
          <ul>
            <h4>Cencus Tract #{this.state.thisTract.index}</h4>
            <li>
              <span style={{ color: "rgb(" + this.state.colors.car + ")" }}>
                <span role="img" aria-label="">
                  🚗 Driving {this.state.mode[0]}
                </span>
              </span>
            </li>

            <li>
              <span style={{ color: "rgb(" + this.state.colors.bike + ")" }}>
                <span role="img" aria-label="">
                  🚴 Cycling {this.state.mode[1]}
                </span>
              </span>
            </li>

            <li>
              <span style={{ color: "rgb(" + this.state.colors.walk + ")" }}>
                <span role="img" aria-label="">
                  🚶 Walking {this.state.mode[2]}
                </span>
              </span>
            </li>

            <li>
              <span style={{ color: "rgb(" + this.state.colors.transit + ")" }}>
                <span role="img" aria-label="">
                  🚌 Transit {this.state.mode[3]}
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
          Predicts mobility choices of simulated individuals based on individual
          characteristics and land use. The choice models are calibrated based
          on census data and the individual choices are influenced by initial
          conditions and by user interactions, as captured by the cityIO server.
          <this._mouseOnTract thisTractIndex={true} />
        </div>
        <DeckGL
          layers={this._Layers()}
          viewState={this.state.viewState}
          onLoad={this._onLoad}
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
