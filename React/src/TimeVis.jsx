import React from "react";
import { XYPlot, ArcSeries } from "react-vis";

function getSeconds() {
  let t = Math.floor(new Date().getTime() / 10);
  return t;
}

export class TimeVis extends React.Component {
  state = {
    time: 0
  };

  componentDidMount() {
    this._timerId = setInterval(
      () => this.setState({ time: getSeconds() }),
      10
    );
  }

  componentWillUnmount() {
    clearInterval(this._timerId);
    this.setState({ timerId: false });
  }

  render() {
    const { time } = this.state;
    const seconds = time % 100;
    const eight = time % 800;
    // const timerText = <Timer timer={this.state.time} />;

    return (
      <div>
        <XYPlot
          xDomain={[-5, 5]}
          yDomain={[-5, 5]}
          width={100}
          height={100}
          getAngle={d => d.time}
          getAngle0={d => 0}
          color={"white"}
        >
          <ArcSeries
            animation={{
              damping: 10
            }}
            radiusDomain={[0, 10]}
            data={[
              {
                time: (seconds / 60) * 4,
                radius0: 1,
                radius: 3
              },
              {
                time: (eight / 800) * 3.14 * 2,
                radius0: 4,
                radius: 8
              }
            ]}
          />
        </XYPlot>
      </div>
    );
  }
}
