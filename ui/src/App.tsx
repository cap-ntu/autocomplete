import React from 'react';

import {
  Container,
  Paper,
  Typography,
  Grid,
} from '@material-ui/core';

import {Pos} from 'codemirror';
import {UnControlled as CodeMirror} from 'react-codemirror2';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';

import fetch from 'isomorphic-fetch';
import {stringify} from 'query-string';

// import logo from './logo.svg';

import './App.css';

export interface AppProps {
  backend?: string;
}

export interface AppState {
  code: string;
}

class App extends React.Component<AppProps, AppState> {
  private options: any;
  private requesting: boolean;

  static defaultProps = {
    backend: 'http://127.0.0.1:9078',
  };

  getHints(cm, options) {
    const cursor = cm.getCursor();
    const line = cm.getLine(cursor.line);
    const data = {
      keyword: line,
      model: '1k_token',
    };
    const predictURL = `${this.props.backend}/predict?${stringify(data)}`;
    console.log(predictURL);

    return new Promise((accept, reject) => {
      setTimeout(() => {
        fetch(predictURL, {
          headers: {
            'Content-Type': 'application/json',
          },
          mode: 'cors',
          method: 'GET',
          cache: 'no-cache',
        }).then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        }).then(data => {
          console.log(data.data.results);
          this.requesting = false;
          accept({
            list: data.data.results,
            from: Pos(cursor.line, 0),
            to: Pos(cursor.line, line.length),
          });
        }).catch(reason => {
          console.log(reason);
          this.requesting = false;
          reject(reason);
        });
      }, 0);
    });
  }

  tabFunction(cm) {
    const cursor = cm.getCursor();
    const line = cm.getLine(cursor.line);
    if (cursor.ch && line[cursor.ch - 1] !== ' ' && cursor.ch === line.length) {
      if (!this.requesting) {
        this.requesting = true;
        cm.showHint();
      }
      return;
    }
    const indentUnit = cm.getOption('indentUnit');
    const spacesNum = indentUnit - cursor.ch % indentUnit;
    const spaces = Array(spacesNum + 1).join(' ');
    cm.replaceSelection(spaces);
  }

  constructor(props: AppProps, context: any) {
    super(props, context);
    this.state = {
      code: '# Start your code here:\n\n',
    };
    this.options = {
      lineNumbers: true,
      styleActiveLine: true,
      matchBrackets: true,
      mode: 'python',
      theme: 'material-darker',
      indentWithTabs: true,
      indentUnit: 4,
      extraKeys: {
        // 'Ctrl-Space': 'autocomplete',
        'Tab': this.tabFunction.bind(this),
      },
      hintOptions: {hint: this.getHints.bind(this)},
      // height: '800px',
    };
    this.requesting = false;
  }

  render() {
    return (
        <Container fixed>
          <Paper className="App-paper">
            <Grid container justify="center" className="App-title">
              <Typography variant="h3">
                Auto Python Suggestion Demo @ NTU
              </Typography>
            </Grid>
            <Grid container justify="center">
              <Grid item xs={12} sm={10}>
                <Typography>
                  The Python code will be completed automatically using LSTM
                  based
                  language models. We have lots of models for you to choose, the
                  number inside the model name is the number of programs we used
                  as training data.
                </Typography>
              </Grid>
            </Grid>
          </Paper>
          <Paper className="App-paper">
            <CodeMirror className="App-codemirror"
                        value={this.state.code} options={this.options}/>
          </Paper>
        </Container>
    );
  }
}

export default App;
