import React from 'react';
import Table from 'react-bootstrap/Table';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Accordion from 'react-bootstrap/Accordion';
import ToggleButton from 'react-bootstrap/ToggleButton';
import ToggleButtonGroup from 'react-bootstrap/ToggleButtonGroup'; 
import { useTable } from 'react-table'

function TestStyledTriangle({ columns, data }) {
  // Use the state and functions returned from useTable to build your UI
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({
    columns,
    data,
  })

   renderTable(triangle) {
      let table = [];
      table.push(
         <Table {...getTableProps()} key={this.state.index} responsive>
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

export default TestStyledTriangle;