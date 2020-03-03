import React from 'react';
import { Route, Switch } from 'react-router-dom'
import HomePage from './pages/HomePage';
import CleanDataPage from './pages/CleanDataPage';
import UploadDataPage from './pages/UploadDataPage';
import ChooseSettingsPage from './pages/ChooseSettingsPage';
import ConnectDataToSheetPage from './pages/ConnectDataToSheetPage';
import CorrectDataPage from './pages/CorrectDataPage';
import CorrectFormatDataPage from './pages/CorrectFormatDataPage';
import ExceptionPage from './pages/ExceptionPage';
import ChooseDimensionPage from './pages/ChooseDimensionPage';



export default function App() {
    return (
        <Switch>
        	<Route exact path="/" component={HomePage} />

        	<Route exact path="/cleandata" component={CleanDataPage} />
        	<Route exact path="/correctdata" component={CorrectDataPage} />

         <Route exact path="/uploaddata" component={UploadDataPage} />
        	<Route exact path="/choosesettings" component={ChooseSettingsPage} />
        	<Route exact path="/choosedimension" component={ChooseDimensionPage} />
         <Route exact path="/connectdata" component={ConnectDataToSheetPage} />

        	<Route exact path="/correctformatdata" component={CorrectFormatDataPage} />
         <Route exact path="/exceptionpage" component={ExceptionPage} />
        </Switch>
    )
}