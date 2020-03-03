import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {

    const divStyle = {
      color: '#D4AF37',
    };

    return (
            <ul className="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion" id="accordionSidebar">

                <a className="sidebar-brand d-flex">
                    <div 
                        style={divStyle}
                        className="sidebar-brand-text mx-3">ReBridge
                    </div>
                </a>

                <hr className="sidebar-divider my-0"/>

                <li className="nav-item">
                    <NavLink className="nav-link active" to="/" >
                        <i className="fas fa-fw fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </NavLink>
                </li>

                <hr className="sidebar-divider"/>

                <div className="sidebar-heading">
                    Data handling 
                </div>

                <li className="nav-item">
                    <NavLink className="nav-link" to="/cleandata" activeClassName="active">
                        <i className="fas fa-fw fa-file-upload"></i>
                        <span>Clean data</span>
                    </NavLink>
                </li>

                <li className="nav-item">
                    <NavLink className="nav-link" to="/uploaddata" activeClassName="active">
                        <i className="fas fa-fw fa-ruler-combined"></i>
                        <span>Format data</span>
                    </NavLink>
                </li>

                <hr className="sidebar-divider d-none d-md-block"/>

                <div className="text-center d-none d-md-inline">
                    <button className="rounded-circle border-0" id="sidebarToggle"></button>
                </div>

                <hr className="sidebar-divider"/>

            </ul>

    );
}
