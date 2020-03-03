import React from 'react';
import { Link } from 'react-router-dom';
import Jexcel from './../../components/Jexcel';


export default function CorrectFormatDataPage() {
  return (
   <div className="hero-unit">
      <Jexcel options={options} />
   </div>
  )
}

var data = [
  ['Jazz', 'Honda', '2019-02-12', '', true, '$ 2.000,00', '#777700'],
  ['Civic', 'Honda', '2018-07-11', '', true, '$ 4.000,01', '#007777'],
];

var options = {
  data:data,
  colHeaders: ['Model', 'Price', 'Price' ],
  // colWidths: [ 300, 300, 300 ],
  columns: [
    { type: 'text', title:'Car', width:"120px" },
    { type: 'dropdown', title:'Make', width:'250px', source:[ "Alfa Romeo", "Audi", "Bmw" ] },
    { type: 'calendar', title:'Available', width:'250px' },
    { type: 'image', title:'Photo', width:'120px' },
    { type: 'checkbox', title:'Stock', width:'80px' },
    { type: 'numeric', title:'Price', width:'100px', mask:'$ #.##,00', decimal:',' },
    { type: 'color', width:'100px', render:'square', }
  ]

};