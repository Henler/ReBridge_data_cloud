import React from 'react';
import Nav from 'react-bootstrap/Nav';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';

class OutputDataBox extends React.Component {
   constructor(props) {
      super(props);

      this.state = {
         showData: true,
         triangle: this.props.triangle,
         activeKey: "data",
      }
      this.handleDataClick = this.handleDataClick.bind(this);
      this.handleDetailsClick = this.handleDetailsClick.bind(this);
      this.handleRoleClick = this.handleRoleClick.bind(this);
   }

   componentWillReceiveProps(nextProps) {
      this.setState({
         triangle: nextProps.triangle,
         showData: true,
         activeKey: "data",
      });
   }


   renderData(triangle) {
      // If statement not needed later - need it since API is currently called
      if (triangle.length == 0) {
         return <p>Here goes data for 1 data table</p>
      }
      else {
         return this.renderTable(triangle)
      }
   }

   handleNameChange(event) {
      this.props.nameCallback(event.target.value);
   }

   handleRoleClick(role, index, e) {
      this.props.roleCallback(role, index)
   }

   renderDetails(triangle) {



      function renderRoles(triangle) {
      return (
         <Form.Group controlId="Name">
            <Form.Label><b>Roles</b></Form.Label>
            <Form.Check 
               type="radio"
               label="None"
               name="formHorizontalRadios"
               id="None"
               defaultChecked={triangle.roles.length == 0 || triangle.roles.indexOf("None") > -1}
               onClick={this.handleRoleClick("None", triangle.id, e)}
            />
            <Form.Check 
               type="radio"
               label="Claim - Paid"
               name="formHorizontalRadios"
               id="paid"
               defaultChecked={triangle.roles.indexOf("Claim - Paid") > -1}
               onClick={this.handleRoleClick("Claim - Paid", triangle.id, e)}
            />
            <Form.Check 
               type="radio"
               label="Claim - Reserved"
               name="formHorizontalRadios"
               id="reserved"
               defaultChecked={triangle.roles.indexOf("Claim - Reserved") > -1}
               onClick={this.handleRoleClick("Claim - Reserved", triangle.id, e)}
            />
            <Form.Check 
               type="radio"
               label="Claim - Incurred"
               name="formHorizontalRadios"
               id="incurred"
               defaultChecked={triangle.roles.indexOf("Claim - Incurred") > -1}
               onClick={this.handleRoleClick("Claim - Incurred", triangle.id, e)}
            />
            <Form.Check 
               type="radio"
               label="Premium"
               name="formHorizontalRadios"
               id="premium"
               defaultChecked={triangle.roles.indexOf("Premium") > -1}
               onClick={(e) => this.handleRoleClick("Premium", triangle.id, e)}
            />
         </Form.Group>
      )}
      let name = triangle.name;
      let originalSheet = ""
      if (triangle.orig_sheet_name != undefined) {
         originalSheet = triangle.orig_sheet_name;
      } else {
         originalSheet = "N/A"
      }
      let placeholder_name = "";
      if (name != 'null') {
         placeholder_name = name;
      }
      let disabled_tag = ""
      if (triangle.type == "output") {
         disabled_tag = "disabled"
      }
      if (!triangle.fit_for_output) {
         disabled_tag = "disabled"
      }

      return (
         <div>
            <Form>
               <Form.Group controlId="Original sheet">
                  <Form.Label><b>Original sheet name</b></Form.Label>
                  <Form.Control plaintext readOnly defaultValue={originalSheet} /> 
               </Form.Group>
               <Form.Group controlId="Name">
                  <Form.Label><b>Name</b></Form.Label>
                  <Form.Control readOnly type="text" placeholder="Enter table name" defaultValue={placeholder_name} onBlur={this.handleNameChange.bind(this)}/>
               </Form.Group>
               <Form.Group controlId="Name">
                  <Form.Label><b>Roles</b></Form.Label>
                  <Form.Check
                     type="radio"
                     label="None"
                     name="formHorizontalRadios"
                     id="None"
                     defaultChecked={triangle.roles.length == 0 || triangle.roles.indexOf("None") > -1}
                     onClick={(e) => this.handleRoleClick("None", triangle.id, e)}
                     disabled={disabled_tag}
                  />
                  <Form.Check
                     type="radio"
                     label="Claim - Paid"
                     name="formHorizontalRadios"
                     id="paid"
                     defaultChecked={triangle.roles.indexOf("Claim - Paid") > -1}
                     onClick={(e) => this.handleRoleClick("Claim - Paid", triangle.id, e)}
                     disabled={disabled_tag}
                  />
                  <Form.Check 
                     type="radio"
                     label="Claim - Reserved"
                     name="formHorizontalRadios"
                     id="reserved"
                     defaultChecked={triangle.roles.indexOf("Claim - Reserved") > -1}
                     onClick={(e) => this.handleRoleClick("Claim - Reserved", triangle.id, e)}
                     disabled={disabled_tag}
                  />
                  <Form.Check 
                     type="radio"
                     label="Claim - Incurred"
                     name="formHorizontalRadios"
                     id="incurred"
                     defaultChecked={triangle.roles.indexOf("Claim - Incurred") > -1}
                     onClick={(e) => this.handleRoleClick("Claim - Incurred", triangle.id, e)}
                     disabled={disabled_tag}
                  />
                  <Form.Check 
                     type="radio"
                     label="Premium"
                     name="formHorizontalRadios"
                     id="premium"
                     defaultChecked={triangle.roles.indexOf("Premium") > -1}
                     onClick={(e) => this.handleRoleClick("Premium", triangle.id, e)}
                     disabled={disabled_tag}
                  />
               </Form.Group>
            </Form>
         </div>
      )
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
      // This only needed since we give unit and output triangles in different formats. Should think about changing that
      if ("ids" in rows[0]) {
         let new_rows = []
         for (let i=0; i<rows.length; i++) {
            new_rows.push(rows[i].values)
         }
         rows = new_rows;
      }
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

   handleDataClick(e) {
      e.preventDefault();
      this.setState({
         showData: true,
         activeKey: "data",
      })
   }

   handleDetailsClick(e) {
      e.preventDefault();
      this.setState({
         showData: false,
         activeKey: "details",
      })
   }



   render() {
      return (
         <Card className="shadow mb-4">
            <Card.Header className="d-block py-3">
               <Nav variant="tabs" defaultActiveKey="data" activeKey={this.state.activeKey}>
                  <Nav.Item>
                     <Nav.Link eventKey="data" onClick={this.handleDataClick}>Data</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                     <Nav.Link eventKey="details" onClick={this.handleDetailsClick}>Details</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                     <Nav.Link eventKey="disabled" disabled>{this.state.triangle.name}</Nav.Link>
                  </Nav.Item>
               </Nav>
            </Card.Header>
            <Card.Body>
               <Row className="border-bottom pb-3">
                 <Col>
                     {this.state.showData ? this.renderData(this.state.triangle) : this.renderDetails(this.state.triangle)}
                 </Col>
               </Row>
            </Card.Body>
         </Card>
      );
   }

}

export default OutputDataBox;