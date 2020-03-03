import React from 'react';
import { Link } from 'react-router-dom';
import UploadDataBox from './../../components/UploadDataBox';

export default function CleanDataPage() {
   return (
   <div className="hero-unit">
      <h1>Clean data</h1>
      Please upload your data<br />
      <div className="row">
         <UploadDataBox />
      </div>
      <div className="row">
         <div className="col">
            <Link className="btn btn-primary" to="/correctdata"> Next </Link>
         </div>
      </div>
   </div>
   );
}