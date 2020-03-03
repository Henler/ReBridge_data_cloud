import React from 'react';
import UnitTriangle from './UnitTriangle';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';



class UnitTriangleBox extends React.Component {
   constructor(props) {
      super(props)
      this.state = {
         index: this.props.index,
         unitTriangles: this.props.unitTriangles,
      }
   }

   render() {
      return (
      <Row>
         <Col>
            <Card className="shadow mb-4">
               <Card.Header className="d-block py-3">
                  <h6 className="m-0 font-weight-bold text-primary">Unit triangles</h6>
               </Card.Header>
               <Card.Body>
                  {this.state.unitTriangles.map((triangle, index) => 
                     <UnitTriangle 
                       key={index} 
                       index={index} 
                       unitTriangle={triangle}
                       unitTriangleCallback={this.props.unitTriangleCallback}
                        />
                  )}
               </Card.Body>
            </Card>
         </Col>
      </Row>
      );
   }
}

export default UnitTriangleBox;