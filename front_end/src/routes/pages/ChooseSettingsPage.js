import React from 'react';
import axios from 'axios';
import mock_data from './../../__mock__/mock_file.json';
import { Link } from 'react-router-dom';
import ChooseSettingsBox from './../../components/ChooseSettingsBox';
import ErrorBox from './../../components/ErrorBox';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';


class ChooseSettingsPage extends React.Component {
   constructor(props) {
      super(props);
        const { data } = this.props.location;
        this.state = {
           settings: [],
           dataHolder: null,
           fileName: data.fileName,
           sr_list: data.sr_list,
           strDataHolderDict: null,
           recievedOutputData: null,
           responseRecieved: false,
           returnedError: false,
           error: null,
           selectedSheets: null,
        }

      this.settingsCallback = this.settingsCallback.bind(this);
      this.buildOutput = this.buildOutput.bind(this);
   }

   settingsCallback(returned_data, finnishLoadingCallback) {
      this.setState({
        settings: returned_data["settings"],
        selectedSheets: returned_data["selectedSheets"]
      });
      this.buildOutput(finnishLoadingCallback); 
   }

   buildOutput(finnishLoadingCallback) {
      const url = 'http://127.0.0.1:8000/triangle_formatting/buildoutput_API'
      const data = {
         triangles: this.state.settings,
         dataHolder: this.state.dataHolder,
         fileName: this.state.fileName,
         selected_sheets: this.state.selectedSheets,
         sr_list: this.state.sr_list,
      }

      axios.post(url, data)
      .then(res => {
         finnishLoadingCallback();
         if ('response_error' in res.data) {
            this.setState({
               returnedError: true,
               error: res.data.response_error,
            })
         } else {
            this.setState({
               recievedOutputData: res.data.data
            });
         }
      })
      .then(() => 
         this.setState({responseRecieved: true})
       )
      .catch(err => {
         this.setState({
            returnedError: true,
            error: err,
         })
      })
   }

   render() {
   let renderedBox;
   if (!this.state.returnedError) {
      renderedBox = <ChooseSettingsBox 
                      parentCallback = {this.settingsCallback} 
                      fileName = {this.state.fileName}
                      sr_list = {this.state.sr_list}
                     />;
   } else {
      renderedBox = <ErrorBox 
                        error = {this.state.error}
                     />;
   }

   return (
   <div className="hero-unit">
      <h5 className="m-1 font-weight-bold text-secondary pb-3 pt-2">Please choose settings</h5>
      <Row>
        {renderedBox}
      </Row>
      <Row className="pt-3 pb-3">
         <Col>
            <Link 
               className={this.state.responseRecieved ? "btn btn-primary" : "btn btn-secondary disabled"} 
               to={{
                  pathname: "/choosedimension",
                  data: {
                     dataHolder: this.state.dataHolder,
                     recievedOutputData: this.state.recievedOutputData,
                     fileName: this.state.fileName,
                     templates: this.state.settings.templates,
                  }
               }}
            > 
               Next
            </Link>

         </Col>
      </Row>
   </div>
   );
   }
}

export default ChooseSettingsPage;