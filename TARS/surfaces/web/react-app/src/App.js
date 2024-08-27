import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import ChatComponent from './components/ChatComponent';
import LoginComponent from './components/LoginComponent';
import DashboardComponent from './components/DashboardComponent';

function App() {
  return (
    <Router>
      <div className="App">
        <Switch>
          <Route path="/login" component={LoginComponent} />
          <Route path="/dashboard" component={DashboardComponent} />
          <Route path="/" component={ChatComponent} />
        </Switch>
      </div>
    </Router>
  );
}

export default App;
