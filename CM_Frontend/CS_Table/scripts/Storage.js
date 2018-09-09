// https://www.sitepoint.com/javascript-design-patterns-singleton/
//https://gist.github.com/dmnsgn/4a6ad76de1b5928f13f68f406c70bb09

class Storage {
  constructor() {
    this._cityIOurl = "";
  }

  //cityIO url
  get cityIOurl() {
    return this._cityIOurl;
  }
  set cityIOurl(value) {
    this._cityIOurl = value;
  }

  //gridCellsArray
  get gridCellsArray() {
    return this._gridCellsArray;
  }
  set gridCellsArray(value) {
    this._gridCellsArray = value;
  }
}

export default new Storage();
