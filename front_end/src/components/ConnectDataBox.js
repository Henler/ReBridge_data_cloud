import React from 'react';
import axios from "axios";

class ConnectDataBox extends React.Component {
   constructor(props) {
      super(props);
      this.RequestData = this.RequestData.bind(this);
   }

   RequestData(event) {
      try {
         axios.get('http://127.0.0.1:8000/triangle_formatting/connectdata_API')
        .then(res => {
            console.log(res);
            console.log(res.data);
         })
      } catch (e) {
        console.log(`😱 Axios request failed: ${e}`);
      }
   }



   render() {
   return (
    <div className="row">
      <div className="col">
        <div className="card shadow mb-4">
          <div className="card-body">
            <div className="row">
              <div className="col">
                <h5><b> Output sheet # </b></h5>
              </div>
            </div>
            <div className="row">
              <div className="col">
                <button
                onClick = {this.RequestData}
                className="btn btn-primary">
                Submit
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    );
   }
}

export default ConnectDataBox;