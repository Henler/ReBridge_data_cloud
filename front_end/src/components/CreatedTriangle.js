import React from 'react';
import Table from 'react-bootstrap/Table';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Accordion from 'react-bootstrap/Accordion';

class CreatedTriangle extends React.Component {
   constructor(props) {
      super(props)
      this.state = {
         index: this.props.index,
      }
      this.renderTable = this.renderTable.bind(this)
      this.renderHeaders = this.renderHeaders.bind(this)
      this.renderRows = this.renderRows.bind(this)
}

   renderTable(triangle) {
      let table = [];
      table.push(
         <Table key={this.state.index} responsive>
            {this.renderHeaders(triangle.headers)}
            {this.renderRows(triangle.rows)}
         </Table>)
      return table
   }


   renderHeaders(headers) {
      let parsed_headers = []
      let children = []
      headers.map((header, index) =>
         children.push(<th key={index}>{header}</th>)
      )
      parsed_headers.push(<thead key={this.state.index}><tr>{children}</tr></thead>);
      return parsed_headers
   }

   renderRows(rows) {
      let parsed_rows = []
      let children = []
      let entries = []

      rows.map((row, index) => {
         row.values.map((entry, index) => {
            if(index == 0) {
               entries.push(
                  <td key={index}>{entry}</td>)
            } else {
               entries.push(
                  <td key={index}>{this.addThousandSeperators(this.removeDecimals(entry))}</td>)
            }
         })
         children.push(<tr key={index}>{entries}</tr>)
         entries = []
      })
      parsed_rows.push(<tbody key={this.state.index}>{children}</tbody>)
      return parsed_rows
   }

   removeDecimals(nmbr) {
      if(isNaN(nmbr)) {
         return nmbr;
      } else {
         return Math.trunc(nmbr);
      };
   }

   addThousandSeperators(nmbr) {
      if(nmbr > 0) {
          return nmbr.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      } else {
          return nmbr;
      }
   }



   render() {
      return (
      <Row>
         <Col>
            <Accordion>
               <Card className="mb-3">
                  <Accordion.Toggle as={Card.Header} eventKey={this.state.index}>
                     <h6 className="m-0 font-weight-bold">
                        🔧 # {this.state.index}: Output 
                     </h6>
                  </Accordion.Toggle>
                  <Accordion.Collapse eventKey={this.state.index}>                 
                  <Card.Body>
                     {this.renderTable(this.props.outputTriangle)}
                  </Card.Body>
                  </Accordion.Collapse>
               </Card>
            </Accordion>
         </Col>
      </Row>
      );
   }
}

export default CreatedTriangle;