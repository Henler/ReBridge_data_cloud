import React from 'react';
import Table from 'react-bootstrap/Table';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Accordion from 'react-bootstrap/Accordion';
import ToggleButton from 'react-bootstrap/ToggleButton';
import ToggleButtonGroup from 'react-bootstrap/ToggleButtonGroup'; 

class UnitTriangle extends React.Component {
   constructor(props) {
      super(props)
      this.state = {
         index: this.props.index,
         triangle: this.props.unitTriangle,
         type: this.props.unitTriangle.roles,
      }
      this.renderTable = this.renderTable.bind(this);
      this.renderHeaders = this.renderHeaders.bind(this);
      this.renderRows = this.renderRows.bind(this);
      this.handleTypeChange = this.handleTypeChange.bind(this);
   }

   // Only getting empty if None but want to send None
   componentDidMount() {
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

   handleTypeChange(val) {
      if(val.length == 0) {
         this.setState({type: "None"})
         this.props.unitTriangleCallback("None", this.state.triangle.id)
      } else {
         this.setState({type: val[val.length-1]})
         this.props.unitTriangleCallback(val[val.length-1], this.state.triangle.id)
      }
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
                     {this.state.type != "None" ? 
                        <h6 className="m-0 font-weight-bold text-primary">
                           {this.state.triangle.orig_sheet_name} - {this.state.triangle.name}
                        </h6>
                        :
                        <h6 className="m-0 font-weight-bold">
                           {this.state.triangle.orig_sheet_name} - {this.state.triangle.name}
                        </h6>
                     }
                  </Accordion.Toggle>
                  <Accordion.Collapse eventKey={this.state.index}>                 
                  <Card.Body>
                    <Row className="border-bottom pb-3">
                      <Col>
                        <ToggleButtonGroup type="checkbox" value={this.state.type} onChange={this.handleTypeChange}>
                          <ToggleButton value={"Claim - Paid"} disabled={!this.state.triangle.fit_for_output}>Claim - Paid</ToggleButton>
                          <ToggleButton value={"Claim - Reserved"} disabled={!this.state.triangle.fit_for_output}>Claim - Reserved</ToggleButton>
                          <ToggleButton value={"Claim - Incurred"} disabled={!this.state.triangle.fit_for_output}>Claim - Incurred</ToggleButton>
                          <ToggleButton value={"Premium"} disabled={!this.state.triangle.fit_for_output}>Premium</ToggleButton>
                        </ToggleButtonGroup>
                      </Col>
                    </Row>
                    <Row>
                      <Col>
                        {this.renderTable(this.state.triangle)}
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

export default UnitTriangle;