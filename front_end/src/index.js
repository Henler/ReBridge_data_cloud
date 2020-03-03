import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter } from 'react-router-dom';
import './static/css/sb-admin-2.min.css';
import '@fortawesome/fontawesome-free/css/all.min.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import Routes from './routes/Routes';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Footer from './components/Footer';

class Index extends React.Component {
   render() {
      return (
         <BrowserRouter>
            <div id="wrapper"> 
               <Sidebar />
               <div id="content-wrapper" className="d-flex flex-column">
                  <div id="content">
                  <Topbar />
                     {/* Main content*/}
                     <div className="container-fluid">
                        <Routes />
                     </div>
                  </div>
                  <Footer />
               </div>
            </div>
         </BrowserRouter>
      );
    }
}

ReactDOM.render(<Index />, document.getElementById('app'));
module.hot.accept();
