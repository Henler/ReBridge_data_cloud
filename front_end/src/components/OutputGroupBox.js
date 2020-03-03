import React from 'react';
import UnitTriangleBox from './UnitTriangleBox';
import CreatedTriangleBox from './CreatedTriangleBox';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';


class OutputGroupBox extends React.Component {
	constructor(props) {
		super(props)
		this.state = {
			index: this.props.index,
		}
      this.identifyOutputGroupTriangles = this.identifyOutputGroupTriangles.bind(this);
      this.identifyUnitGroupTriangles = this.identifyUnitGroupTriangles.bind(this);
	}

   identifyOutputGroupTriangles(groupIndex, outputTriangles) {
      let matchingTriangles = [];
      {outputTriangles.map((triangle) => {
         if(triangle.group_id == groupIndex) {
            matchingTriangles.push(triangle);
         }
      }
      );}
      return matchingTriangles
   }

   identifyUnitGroupTriangles(groupIndex, outputTriangles) {
      let matchingTriangles = [];
      {outputTriangles.map((triangle) => {
         if(triangle.card_id == groupIndex) {
            matchingTriangles.push(triangle);
         }
      }
      );}
      return matchingTriangles
   }

	render() {
		return (
		<Col>
        	<Card className="shadow mb-4">
            <Card.Body>
               <Row>
                  <Col>
                     <h5><b> Output sheet # {this.props.index+1} </b></h5>
                  </Col>
               </Row>
               <Row>
                  <Col lg={6}>
                     <Col lg={12}>
                        <UnitTriangleBox 
                           key={this.props.index}
                           index={this.props.index} 
                           unitTriangles={this.identifyUnitGroupTriangles(
                              this.props.index,
                              this.props.unitTriangles)

                           }
                           outputTriangles={this.identifyOutputGroupTriangles(
                              this.props.index, 
                              this.props.outputTriangles)
                           }
                           unitTriangleCallback={this.props.unitTriangleCallback} 
                        />
                     </Col>
                  </Col>
                  <Col lg={6}>
                     <Col lg={12}>
                        <CreatedTriangleBox 
                           key={this.props.index}
                           index={this.props.index}
                           outputTriangles={this.identifyOutputGroupTriangles(
                              this.props.index, 
                              this.props.outputTriangles)
                           }
                        />
                     </Col>
                  </Col>
               </Row>
            </Card.Body>
         </Card>
      </Col>
		);
	}
}

export default OutputGroupBox;