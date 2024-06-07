import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    axios.get('http://localhost:8000/api/endpoint') // Replace 'http://localhost:8000/api/endpoint' with the actual API endpoint
      .then(response => setData(response.data))
      .catch(error => console.error("There was an error!", error));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>React UI for TARS APIs</h1>
        {data && <div>{JSON.stringify(data)}</div>}
      </header>
    </div>
  );
}

export default App;
