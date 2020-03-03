import React from 'react';
import axios from 'axios';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Spinner from 'react-bootstrap/Spinner';

class UploadDataBox extends React.Component {
   constructor(props) {
      super(props);
      this.state = {
         selectedFile: null,
         fileUploaded: false,
         fileUploadInProgress: false,
         error: null,
         returnedError: false,
      };
      
      this.handleSubmit = this.handleSubmit.bind(this);
      this.handleChange = this.handleChange.bind(this);
   }

   handleSubmit(event) {
      event.preventDefault();

      this.setState({fileUploadInProgress: true});
      let data = new FormData();
      const url = "http://127.0.0.1:8000/triangle_formatting/recive_sheets_and_name_API"
      data.append("file", this.state.selectedFile);

      axios.post(url, data, {
         headers: {
            'Content-Type': 'application/multipart/form-data'
         }
         })
         .then(res => {
            this.setState({fileUploadInProgress: false});
            this.props.parentCallback(res.data);
        })
         .catch(err=> {
            console.log(err);
            this.setState({
               returnedError: true,
               fileUploadInProgress: false,
               error: err,
            });
         })
   }

   handleChange(event) {
      event.preventDefault();
      this.setState({
         selectedFile: event.target.files[0],
         fileUploaded: true,
    })
   }

   shortenErrorMessage(message) {
      return message.substring(0, message.indexOf("C"))
   }

   render() {
      return (
      <Col xl={12} md={12} mb={4}>
         <Card className="shadow mb-4">
            <Card.Header className="d-block py-3">
               <h6 className="m-0 font-weight-bold text-primary">Upload data</h6>
            </Card.Header>
            <Card.Body>
               <form 
                  onSubmit={this.handleSubmit} 
                  onChange={this.handleChange}>
                  <label>
                      Upload file:
                      <input type="file"/>
                   </label>
                   <br />
                   <button 
                        type="submit" 
                        className={this.state.fileUploaded ? 'btn btn-primary' : 'btn btn-secondary'}>
                        {this.state.fileUploadInProgress ? 
                        <Spinner
                           as="span"
                           animation="border"
                           size="sm"
                           role="status"
                           aria-hidden="true"
                        /> : 
                        ""}
                        <a> Submit</a>
                   </button>
                   {this.state.returnedError && 
                     <Row className="border-top mt-3 pb-3">
                        <h6 className="mt-3 font-weight-bold text-primary">Ops, an error occured...</h6>
                        <div className="mt-3"> {this.shortenErrorMessage(this.state.error.response.data)} </div>
                     </Row>
                  }
               </form>
            </Card.Body>
         </Card>
       </Col>

       );
   }
}

export default UploadDataBox;