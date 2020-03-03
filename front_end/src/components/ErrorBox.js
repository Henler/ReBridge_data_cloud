import React from 'react';
import axios from "axios";
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Table from 'react-bootstrap/Table';
import ErrorTriangle from './ErrorTriangle';

class ErrorBox extends React.Component {
   constructor(props) {
      super(props);

      this.state = {
         message: this.props.error.message,
         dataHolder: this.props.error.dh,
      }

      this.renderTables = this.renderTables.bind(this);
   }

   renderTables(dh) {
      let table = [];
      dh.map((table_data, index) => 
         table.push(
            <ErrorTriangle
               table_data={table_data}>
            </ErrorTriangle>)
      )

      return table
   }

   render() {
   return (
    <Col xl={12} md={12} mb={4}>
      <Card className="shadow mb-4">

         <Card.Header className="d-block py-3">
            <h6 className="m-0 font-weight-bold text-primary"> {this.state.message} </h6>
         </Card.Header>
            <Card.Body>

               <Row className="border-bottom pb-3">
                 <Col>
                   <p> Additional pre-processing might be needed </p>                   
                   <p> Consider trying: </p>                   
                   <p> - Removing non-essential sheets </p>                   
                   <p> - Removing large chunks of irrelevant data </p>               
                  </Col>
               </Row>

               <Row className="border-bottom pt-3 pb-3">
                  <Col>
                     {this.renderTables(this.state.dataHolder)}
                  </Col>
               </Row>

            </Card.Body>
         </Card>
      </Col>
   );
   }
}

export default ErrorBox;