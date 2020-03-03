import React from 'react';
import axios from "axios";
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import ToggleButton from 'react-bootstrap/ToggleButton';
import ToggleButtonGroup from 'react-bootstrap/ToggleButtonGroup'; 
import Spinner from 'react-bootstrap/Spinner'; 
import ButtonToolbar from 'react-bootstrap/ButtonToolbar';

class ChooseSettingsBox extends React.Component {
   constructor(props) {
      super(props);

      this.state =  {
         settingsSubmited: false,
         type: "single",
         selectedSheets: null,
         returnedError: false,
         exactNumberofSheets: 1,
         inputFormat: ['triangle'],
         exactTypesOfOutputs: ['Claims' , 'Premiums'],
         dataHolder: null,
         error: null,
         settingsSubmissionInProgress: false,
      }
      
      this.handleTypeChange = this.handleTypeChange.bind(this);
      this.handleSelectedSheetsChange = this.handleSelectedSheetsChange.bind(this);
      this.handleExactNumberOfSheetsChange = this.handleExactNumberOfSheetsChange.bind(this);
      this.handleExactTypesOfOutputs = this.handleExactTypesOfOutputs.bind(this);
      this.handleFormatChange = this.handleFormatChange.bind(this);
      this.submitSettings = this.submitSettings.bind(this);
      this.finnishLoading = this.finnishLoading.bind(this);
   }

   componentDidMount() {
      let sheets = [];
      JSON.parse(this.props.sr_list).map(sheet => sheets.push(sheet.sheet_name));
      this.setState({selectedSheets: sheets});
   }

   submitSettings(event) {
      this.setState({settingsSubmissionInProgress: true});

      const settingsUrl = 'http://127.0.0.1:8000/triangle_formatting/settings_API'
      const settingsData = {
         type: this.state.type,
         nmbr_outputs: this.state.exactNumberofSheets,
         outputFormats: this.state.exactTypesOfOutputs
      }

      axios.all([
         axios.post(settingsUrl, settingsData),
      ])
      .then(res => {
         let returned_data = {
            settings: res[0]["data"],
            selectedSheets: this.state.selectedSheets
         };
         returned_data.settings.inputFormat = this.state.inputFormat;
         this.props.parentCallback(returned_data, this.finnishLoading)
      })
      .catch(err => {
         this.setState({
            returnedError: true,
            settingsSubmissionInProgress: false,
            error: err,
         })
      })
   }

   finnishLoading() {
      this.setState({settingsSubmissionInProgress: false});
   }


   handleExactNumberOfSheetsChange(val) {
    this.setState({exactNumberofSheets: val[val.length-1]});
   }

   handleExactTypesOfOutputs(val)  {
    this.setState({exactTypesOfOutputs: val});
   }

   handleTypeChange(val) {
    this.setState({type: val[val.length-1]});
   }

   handleSelectedSheetsChange(val) {
    this.setState({selectedSheets: val});
   }

   handleFormatChange(val) {
      this.setState({inputFormat: val[val.length-1]});
   }


   renderSheetList(sheetList) {
      let sheets = []
      let sheetGroup = []
      sheetList.map((sheet, index) => {
         sheets.push(<ToggleButton style={{flex: 1}} key={index} value={sheet.sheet_name}>{sheet.sheet_name}</ToggleButton>)
         if (index % 4 == 0 && index > 0) {
            sheetGroup.push(
            <ToggleButtonGroup key={index} style={{display: 'flex'}} type="checkbox" value={this.state.selectedSheets} onChange={this.handleSelectedSheetsChange}>
               {sheets}
            </ToggleButtonGroup>);
            sheets = [];
         }
      })
      sheetGroup.push(
      <ToggleButtonGroup key={0} style={{display: 'flex'}} type="checkbox" value={this.state.selectedSheets} onChange={this.handleSelectedSheetsChange}>
         {sheets}
      </ToggleButtonGroup>);
      return sheetGroup
   }

   renderNumberOfSheetsSelection() {
      let sheetSelection = []
      sheetSelection.push(
         <Row className="border-bottom pb-3">
            <Col>
               <p>Select exact number of outputs</p>
               <ToggleButtonGroup type="checkbox" value={this.state.exactNumberofSheets} onChange={this.handleExactNumberOfSheetsChange}>
                  <ToggleButton value={1}>1</ToggleButton>
                  <ToggleButton value={2}>2</ToggleButton>
                  <ToggleButton value={3}>3</ToggleButton>
                  <ToggleButton value={4}>4</ToggleButton>
                  <ToggleButton value={5}>5</ToggleButton>
                  <ToggleButton value={6}>6</ToggleButton>
                  <ToggleButton value={7}>7</ToggleButton>
                  <ToggleButton value={8}>8</ToggleButton>
               </ToggleButtonGroup>
            </Col>
         </Row>)
      return sheetSelection
   }

   renderTypeOfAggregate() {
      let buttonGroup = []
      buttonGroup.push(
         <Row className="border-bottom pt-3 pb-3">
            <Col>
               <p>Do you want premiums and claims?</p>
               <ToggleButtonGroup type="checkbox" value={this.state.exactTypesOfOutputs} onChange={this.handleExactTypesOfOutputs}>
                  <ToggleButton value={'Claims'}>Claims</ToggleButton>
                  <ToggleButton value={'Premiums'}>Premiums</ToggleButton>
               </ToggleButtonGroup>
            </Col>
         </Row>)
      return buttonGroup
   }


   render() {
   return (
    <Col xl={12} md={12} mb={4}>
      <Card className="shadow mb-4">

         <Card.Header className="d-block py-3">
            <h6 className="m-0 font-weight-bold text-primary">Please select settings to generate output</h6>
         </Card.Header>
            <Card.Body>

               <Row className="border-bottom pt-3 pb-3">
                 <Col>
                   <p>Select sheets to be included in analysis</p>
                   {this.renderSheetList(JSON.parse(this.props.sr_list))}
                 </Col>
               </Row>

               {this.renderNumberOfSheetsSelection()}

               <Row className="border-bottom pt-3 pb-3">
                 <Col>
                     <p>Is the input in triangle or table format?</p>
                     <ToggleButtonGroup type="checkbox" value={this.state.inputFormat} onChange={this.handleFormatChange}>
                        <ToggleButton value={"triangle"}>Triangle</ToggleButton>
                        <ToggleButton value={"table"}>Table</ToggleButton>
                     </ToggleButtonGroup>
                 </Col>
               </Row>

                <Row className="border-bottom pt-3 pb-3">
                 <Col>              
                   <p>Choose type of output</p>
                   <ToggleButtonGroup type="checkbox" value={this.state.type} onChange={this.handleTypeChange}>
                     <ToggleButton value={"aggregate"}>Aggregated</ToggleButton>
                     <ToggleButton value={"single"}>Single</ToggleButton>
                   </ToggleButtonGroup>
                 </Col>
                </Row>

               {this.state.type == 'aggregate' ? this.renderTypeOfAggregate() : ""}

                <Row className="pt-3 pb-3">
                   <Col>
                     <button 
                        onClick={this.submitSettings}
                        type="submit" 
                        className={this.state.settingsSubmited ? 'btn btn-secondary' : 'btn btn-primary'}>
                        {this.state.settingsSubmissionInProgress ? 
                        <Spinner
                           as="span"
                           animation="border"
                           size="sm"
                           role="status"
                           aria-hidden="true"
                        /> : 
                        ""}
                        <a> Submit</a>

                     </button>
                   </Col>
                 </Row>

                  {this.state.returnedError && 
                  <Row className="border-top mt-3 pb-3">
                     <h6 className="mt-3 font-weight-bold text-primary">Ops, an error occured...</h6>
                     <div className="mt-3">Error in loading settings</div>
                  </Row>
                  }

            </Card.Body>
         </Card>
      </Col>
   );
   }
}

export default ChooseSettingsBox;