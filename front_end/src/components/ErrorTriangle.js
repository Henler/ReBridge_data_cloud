import React from 'react';
import Table from 'react-bootstrap/Table';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Accordion from 'react-bootstrap/Accordion';
import ToggleButton from 'react-bootstrap/ToggleButton';
import ToggleButtonGroup from 'react-bootstrap/ToggleButtonGroup'; 

class ErrorTriangle extends React.Component {
   constructor(props) {
      super(props)
      this.state = {
         index: this.props.table_data.id,
         triangle_data: this.props.table_data,
         type: this.props.table_data.roles,
      }

      this.renderTable = this.renderTable.bind(this);
      this.renderHeaders = this.renderHeaders.bind(this);
      this.renderRows = this.renderRows.bind(this);
   }

   // Only getting empty if None but want to send None
   componentWillMount() {
      if (this.state.type.length == 0) {
         this.setState({
            type: "None",
         })
      }
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
      let parsedRows = []
      let children = []
      let entries = []

      rows.map((row, index) => {
         row.map((entry, index) => 
            entries.push(
               <td key={index}>{this.addThousandSeperators(this.removeDecimals(entry))}</td>)
            )
         children.push(<tr key={index}>{entries}</tr>)
         entries = []
      })
      parsedRows.push(<tbody key={this.state.index}>{children}</tbody>)
      return parsedRows
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
                        {this.state.triangle_data.orig_sheet_name}
                     </h6>
                  </Accordion.Toggle>
                  <Accordion.Collapse eventKey={this.state.index}>                 
                  <Card.Body>
                    <Row className="border-bottom pb-3">
                      <Col>
                        <p> <b>Sheet name:</b> {this.state.triangle_data.orig_sheet_name} </p>
                        <p> <b>Sheet id:</b> {this.state.triangle_data.id} </p>
                        <p> <b>Sheet identified role:</b> {this.state.type} </p>
                      </Col>
                    </Row>
                    <Row>
                      <Col>
                        {this.renderTable(this.state.triangle_data)}
                      </Col>
                    </Row>
                  </Card.Body>
                  </Accordion.Collapse>
               </Card>
            </Accordion>
         </Col>
      </Row>
      );
   }
}

export default ErrorTriangle;