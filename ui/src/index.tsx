import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import * as serviceWorker from './serviceWorker';

import {CssBaseline, MuiThemeProvider} from '@material-ui/core';
import {createMuiTheme} from '@material-ui/core';
import {blueGrey} from '@material-ui/core/colors';


import 'typeface-roboto';
import 'source-code-pro/source-code-pro.css'

import 'codemirror/lib/codemirror.css';
import 'codemirror/theme/material-darker.css';
import 'codemirror/mode/python/python';

import './index.css';

const theme = createMuiTheme({
  palette: {
    type: 'dark',
    primary: {
      main: blueGrey[600],
    },
  },
});

ReactDOM.render(
    <React.StrictMode>
      <MuiThemeProvider theme={theme}>
        <CssBaseline/>
        <App/>
      </MuiThemeProvider>
    </React.StrictMode>,
    document.getElementById('root'),
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
