import React from 'react';
import CreatedTriangle from './CreatedTriangle';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';

class CreatedTriangleBox extends React.Component {
   constructor(props) {
      super(props)
      this.state = {
         index: this.props.index,
      }
}


   render() {
      return (
      <Row>
         <Col>
            <Card className="shadow mb-4">
               <Card.Header className="d-block py-3">
                  <h6 className="m-0 font-weight-bold text-primary">Created triangles</h6>
               </Card.Header>
               <Card.Body>
                  {this.props.outputTriangles.map((triangle, index) =>
                     <CreatedTriangle 
                        key={index}
                        index={index}
                        outputTriangle={triangle} 
                     />)}
               </Card.Body>
            </Card>
         </Col>
      </Row>
      );
   }
}

export default CreatedTriangleBox;