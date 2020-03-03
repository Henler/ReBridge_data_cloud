import React from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import ErrorBox from './../../components/ErrorBox';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import ToggleButtonGroup from 'react-bootstrap/ToggleButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';
import ButtonToolbar from 'react-bootstrap/ButtonToolbar';
import Button from 'react-bootstrap/Button';
import Accordion from 'react-bootstrap/Accordion';
import Nav from 'react-bootstrap/Nav';
import Form from 'react-bootstrap/Form';
import OutputToolbar from './../../components/OutputToolbar';
import OutputDataBox from './../../components/OutputDataBox';

class ChooseDimensionPage extends React.Component {
   constructor(props) {
      super(props);

      const { data } = this.props.location
      this.state = {
         dataHolder: data.dataHolder,
         fileName: data.fileName,
         recievedOutputData: data.recievedOutputData,
         groupIds: data.recievedOutputData.group_ids,
         outputTriangles: data.recievedOutputData.output_triangles,
         strDataHolder: data.recievedOutputData.str_data_holder,
         unitTriangles: data.recievedOutputData.unit_triangles,
         selectedTriangle: data.recievedOutputData.unit_triangles[0],
         strDataHolderDict: data.recievedOutputData.str_data_holder_dict,
         outputNames: [],
         toolbarNames: this.initializeSettings(data.recievedOutputData.group_ids, data.recievedOutputData.unit_triangles, data.recievedOutputData.output_triangles),
         showData: [],
         change: {
            id: null,
            value: null,
         },
         templates: data.templates,
      }

      this.toolbarCallback = this.toolbarCallback.bind(this);
      this.dataBoxCallback = this.dataBoxCallback.bind(this);
      this.changeNameCallback = this.changeNameCallback.bind(this);
      this.updateOutputTriangles = this.updateOutputTriangles.bind(this);
      this.updateSegmentationCallback = this.updateSegmentationCallback.bind(this);
   }


   toolbarCallback(selectedTriangle) {
      this.setState({
         selectedTriangle: selectedTriangle
      })
   }

   dataBoxCallback(type, index) {
      let newChange = {
         value: type,
         id: index,
      };
      let new_state = Object.assign({}, this.state); 
      let newSelectedTriangle = new_state.selectedTriangle;
      newSelectedTriangle.roles = type;
      this.setState({
         selectedTriangle: newSelectedTriangle,
      })
      //Update role in unit triangles here 
      this.updateTables(this.state.strDataHolder, newChange, this.state.outputTriangles, this.state.fileName);
   }

   updateTables(input, change, output, filename) {
      const url = 'http://127.0.0.1:8000/triangle_formatting/update_API'
      const data = {
        input: input,
        change: change,
        output: output,
        filename: filename,
      }
      try {
        axios.post(url, data)
        .then(res => {
            this.setState({outputTriangles: res.data.output})
            this.updateOutputTriangles(this.state.toolbarNames, res.data.output)
         })
      } catch (e) {
        console.log(`😱 Axios request failed: ${e}`);
      }
   }

   updateSegmentationCallback(strDataHolder) {

      // All of bellow needs to be done
      const url = 'http://127.0.0.1:8000/triangle_formatting/change_dimension_API'
      const data = {
         str_data_holder: strDataHolder,
         templates: this.state.templates,
      }

      axios.post(url, data)
      .then(res => {
         this.setState({
            groupIds: res.data.data.group_ids,
            outputTriangles: res.data.data.output_triangles,
            unitTriangles: res.data.data.unit_triangles,
            toolbarNames: this.initializeSettings(res.data.data.group_ids, res.data.data.unit_triangles, res.data.data.output_triangles),
         })
      })
      .catch(err => {
         console.log(err)
      })
   }

   changeNameCallback(name) {
      // Copy toolbar to replace in new outputs
      let new_state = Object.assign({}, this.state); 
      let newToolbarNames = new_state.toolbarNames;

      for (let i=0; i < this.state.toolbarNames.length; i++) {
         for (let j=0; j < this.state.toolbarNames[i].unitTriangles.length; j++) {
            if (this.state.toolbarNames[i].unitTriangles[j].name == this.state.selectedTriangle.name) {
               newToolbarNames[i].unitTriangles[j].name = name;
            }
         }
         for (let j=0; j < this.state.toolbarNames[i].outputTriangles.length; j++) {
            if (this.state.toolbarNames[i].unitTriangles[j].name == this.state.selectedTriangle.name) {
               newToolbarNames[i].unitTriangles[j].name = name;
            }
         }
      }
      this.setState({
         toolbarNames: newToolbarNames,
      })
   }

   initializeSettings(groupIds, unitTriangles, outputTriangles) {

      let names = []
         for (let i=0; i<groupIds.length; i++) {
            names.push({
               groupId: groupIds[i],
               groupName: "Output #" + groupIds[i],
               unitTriangles: [],
               outputTriangles: [],
            })
            for (let j=0; j<unitTriangles.length; j++) {
               if (unitTriangles[j].card_id == groupIds[i]) {
                  unitTriangles[j].type = "unit"
                  names[i].unitTriangles.push(unitTriangles[j])
               }
            } 
            for (let j=0; j<outputTriangles.length; j++) {
               if (outputTriangles[j].group_id == groupIds[i]) {
                  if ("Premium" in outputTriangles[j].categories) {
                     outputTriangles[j].name = "Premium"
                  } else {
                     outputTriangles[j].name = "Claim"
                  }
                  outputTriangles[j].roles = "None"
                  outputTriangles[j].type = "output"
                  names[i].outputTriangles.push(outputTriangles[j])
               } 
            }
         }
      return names;
   }

   updateOutputTriangles(oldToolbarNames, outputTriangles) {
      // Copy toolbar to replace in new outputs
      let new_state = Object.assign({}, this.state); 
      let newToolbarNames = new_state.toolbarNames;

      for (let i=0; i < oldToolbarNames.length; i++) {
         let newOutputTriangles = []
         for (let j=0; j < outputTriangles.length; j++) {
            if (oldToolbarNames[i].groupId == outputTriangles[j].group_id) {
               newOutputTriangles.push(outputTriangles[j])
            }
         }
         newToolbarNames[i].outputTriangles = newOutputTriangles
      }

      this.setState({
         toolbarNames: newToolbarNames,
      })
   }


   render() {
   return (
   <div className="hero-unit">
      <Row className="pt-3 pb-3"> 
         <Col xs={9}>
            <OutputDataBox
               triangle = {this.state.selectedTriangle}
               roleCallback = {this.dataBoxCallback}
               nameCallback = {this.changeNameCallback}
            />
         </Col>
         <Col xs={3}>
            <OutputToolbar
               names = {this.state.toolbarNames}
               callback = {this.toolbarCallback}
               segmentations = {this.state.strDataHolderDict}
               segmentationCallback = {this.updateSegmentationCallback}
            />
         </Col>   
      </Row>
   </div>
   );
   }
}

export default ChooseDimensionPage;