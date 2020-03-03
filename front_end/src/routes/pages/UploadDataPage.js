import React from 'react';
import { Link } from 'react-router-dom';
import { Redirect } from 'react-router-dom';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import UploadDataBox from './../../components/UploadDataBox';

class UploadDataPage extends React.Component {
   constructor(props) {
      super(props);
      this.state = {
         sr_list: null,
         fileName: null,
         fileUploaded: false,
      }

      this.fileUploadCallback = this.fileUploadCallback.bind(this);
   }

   fileUploadCallback(returnedData) {
      this.setState({
        fileName: returnedData.dhName,
        sr_list: returnedData.sr_list,
        fileUploaded: true
      });
   }

   render() {
   return (
	<div className="hero-unit">
      <h5 className="m-1 font-weight-bold text-secondary pb-3 pt-2">Please upload your data</h5>
    	<Row>
    		<UploadDataBox parentCallback = {this.fileUploadCallback} />
    	</Row>
   	<Row>
    		<Col>
    			<Link 
               className={this.state.fileUploaded ? "btn btn-primary" : "btn btn-secondary disabled"}
               to={{
                  pathname: "/choosesettings",
                  data: {
                     sr_list: this.state.sr_list,
                     fileName: this.state.fileName,
                  }
               }}
            >
               Next
            </Link>
    		</Col>
    	</Row>
	</div>
   );
   }
}

export default UploadDataPage;