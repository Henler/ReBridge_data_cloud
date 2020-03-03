import React from 'react';
import axios from "axios";
import OutputGroupBox from './../../components/OutputGroupBox';
import { Link } from 'react-router-dom';
import mock_data from './../../__mock__/mock_data.json';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';


class ConnectDataToSheetPage extends React.Component {
	constructor(props) {
		super(props)

       const { data } = this.props.location
       this.renderOutputGroupBoxes = this.renderOutputGroupBoxes.bind(this);
       this.state = {
          dataHolder: data.dataHolder,
          fileName: data.fileName,
          recievedOutputData: data.recievedOutputData,
          groupIds: data.recievedOutputData.group_ids,
          outputTriangles: data.recievedOutputData.output_triangles,
          strDataHolder: data.recievedOutputData.str_data_holder,
          unitTriangles: data.recievedOutputData.unit_triangles,
          change: {
            id: null,
            value: null,
          }
       }
      this.unitTriangleCallback = this.unitTriangleCallback.bind(this);
      this.updateTables = this.updateTables.bind(this);
	}

  unitTriangleCallback(type, index) {
    // Important to call updateTables with newChange since calling with this.state.change does not 
    let newChange = {
      value: type,
      id: index,
    };
    this.setState({change: newChange});
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
            console.log(res)
            this.setState({outputTriangles: res.data.output})
         })
      } catch (e) {
        console.log(`😱 Axios request failed: ${e}`);
      }
  }


   renderOutputGroupBoxes(groupIds) {
      const ids = groupIds;
      let rendered_boxes = [];
      for(let i = 0; i < ids.length; i++) {
         rendered_boxes.push(
            <Row 
               key={i}
            >
               <OutputGroupBox 
                  index={i}
                  outputTriangles={this.state.outputTriangles}
                  unitTriangles={this.state.unitTriangles}
                  unitTriangleCallback={this.unitTriangleCallback}
               />
            </Row>
         );
      }
      return rendered_boxes
   }

	render() {
   return (
   <div className="hero-unit">
      <Row>
         <Col md={{ span: 6 }}>
            <h5 className="m-1 font-weight-bold text-secondary pb-3 pt-2">Please select correct data</h5>
         </Col>
      </Row>
      {this.renderOutputGroupBoxes(this.state.groupIds)}
   </div>
   );
   }
}

export default ConnectDataToSheetPage;