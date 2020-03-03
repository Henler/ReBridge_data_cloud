import React from 'react';
import Accordion from 'react-bootstrap/Accordion';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Badge from 'react-bootstrap/Badge';

class OutputToolbar extends React.Component {
   constructor(props) {
      super(props);

      this.state = {
         menuSelection: null,
         names: this.props.names,
         segmentation: this.props.segmentations,
      }
   }

   componentWillReceiveProps(nextProps) {
      this.setState({
         names: nextProps.names,
      });
   }

   selectMenuItem(name) {
      this.setState({
         menuSelection: name,
      });
   }

   clickHandler(triangle, e) {
      e.preventDefault();
      this.selectMenuItem(triangle.name);
      this.props.callback(triangle)
   }

   segmentationClickHandler(key, value, e) {
      e.preventDefault();
      this.props.segmentationCallback(value)
   }


   renderOutputs(names) {
      let output_groups = []
      // Useless (if-) function needed for testing with API (since function called first without input)
      if (names.length != 0) {
         names.map((group, i) => {
            let outputTriangles = []
            let unitTriangles = []
            group.outputTriangles.map((triangle, j) => {
               //Need to add in name for output triangles as well
               outputTriangles.push(<p onClick={(e) => this.clickHandler(triangle, e)}> {this.state.menuSelection == triangle.name ? "☑️" : "📥"} {triangle.name}</p>);
            })
            group.unitTriangles.map((triangle, j) => {
               unitTriangles.push(<p onClick={(e) => this.clickHandler(triangle, e)}> {this.state.menuSelection ==  triangle.name ? "☑️" : "✏️"} {triangle.name} <Badge variant="info">{triangle.roles == "None" ? "" : triangle.roles}</Badge></p>);
            })
            output_groups.push(
               <Accordion>
                 <Card>
                   <Accordion.Toggle as={Card.Header} eventKey="1">
                     <b>{group.groupName}</b>
                     <Button variant="outline-primary" className="float-right">⚙️</Button>
                   </Accordion.Toggle>
                   <Accordion.Collapse eventKey="1">
                     <Card.Body>
                        <a><b>Output triangles</b></a>
                        {outputTriangles}
                        <hr className="sidebar-divider"/>
                        <a><b>Identified data</b></a>
                        {unitTriangles}
                     </Card.Body>
                   </Accordion.Collapse>
                 </Card>
               </Accordion>
            );
         })
      }

      return output_groups
   }

   renderSegmentations(segmentations) {
      let segments = []
      for (let [key, value] of Object.entries(segmentations)) {
         segments.push(<p onClick={(e) => this.segmentationClickHandler(key, value, e)}> {key.substr(4)} </p>)
      }
      return segments
   }


   render() {
      return (
         <Card className="shadow mb-4">
            <Card.Header className="d-block py-3">
               <h6 className="m-0 font-weight-bold text-primary">Toolbox</h6>
            </Card.Header>
            <Card.Body>
               {this.renderOutputs(this.state.names)}

               <hr className="sidebar-divider"/>

               <Accordion>
                 <Card>
                   <Accordion.Toggle as={Card.Header} eventKey="1">
                     <b>Segmentations</b>
                   </Accordion.Toggle>
                   <Accordion.Collapse eventKey="1">
                     <Card.Body>
                        {this.renderSegmentations(this.state.segmentation)}
                     </Card.Body>
                   </Accordion.Collapse>
                 </Card>
               </Accordion>
            </Card.Body>
         </Card>
      );
   }
}


export default OutputToolbar;