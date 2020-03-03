import React from 'react';
import { Link } from 'react-router-dom';
import jexcel from 'jexcel';
import ReactDOM from 'react-dom';

export default class Jexcel extends React.Component {
    constructor(props) {
        super(props);
        this.options = props.options;
    }

    componentDidMount = function() {
        this.el = jexcel(ReactDOM.findDOMNode(this).children[0], this.options);
    }

    addRow = function() {
        this.el.insertRow();
    }

    render() {
        return (
            <div>
                <div></div><br/>
                <input type='button' value='Add new row' onClick={() => this.addRow()}></input>
            </div>
        );
    }
}
