import React from 'react';
import {
  Container,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Typography,
} from '@material-ui/core';

import {Pos} from 'codemirror';
import {UnControlled as CodeMirror} from 'react-codemirror2';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import fetch from 'isomorphic-fetch';

import './App.css';

export interface AppProps {
  backend: string;
}

export interface AppState {
  code: string;
  language: string;
  model: string;
  models: Array<string>;
  guess: number;
  lines: number;
}

class App extends React.Component<AppProps, AppState> {
  private cm: any;
  private options: any;
  private languages: Array<string>;
  private requesting: boolean;

  static trim(s) {
    return (s || '').replace(/^\s+|\s+$/g, '');
  }

  getKeyword(cm) {
    const cursor = cm.getCursor();
    let result = cm.getLine(cursor.line).substring(0, cursor.ch);
    for (let i = 0, currentLine = cursor.line - 1;
         i < this.state.lines && currentLine >= 0;
         i++, currentLine--) {
      const line = cm.getLine(currentLine);
      const trimmedLine = App.trim(line);
      if (trimmedLine.length > 0 && trimmedLine[0] !== '#') {
        result = line + '\n' + result;
      } else {
        i--;
      }
    }
    console.log(result);
    return result;
  }

  getHints(cm, options) {
    const cursor = cm.getCursor();
    const line = cm.getLine(cursor.line);
    const data = {
      keyword: this.getKeyword(cm),
      model: this.state.model,
      guess: this.state.guess,
    };
    const predictURL = `${this.props.backend}/predict`;

    return new Promise((accept, reject) => {
      setTimeout(() => {
        const failed = () => {
          accept({
            list: [
              App.trim(line),
              'Backend error: Please retry or change a model!',
            ],
            from: Pos(cursor.line, line.search(/\S|$/)),
            to: Pos(cursor.line, cursor.ch),
          });
        };
        fetch(predictURL, {
          headers: {
            'Content-Type': 'application/json',
          },
          mode: 'cors',
          method: 'POST',
          cache: 'no-cache',
          body: JSON.stringify(data),
        }).then((response) => {
          if (!response.ok) {
            console.log(response.statusText);
            this.requesting = false;
            failed();
            return null;
          }
          return response.json();
        }).then(data => {
          if (data && data.data && data.data.hasOwnProperty('results')) {
            console.log(data.data.results);
            this.requesting = false;
            accept({
              list: data.data.results,
              from: Pos(cursor.line, line.search(/\S|$/)),
              to: Pos(cursor.line, cursor.ch),
            });
          } else {
            this.requesting = false;
            failed();
          }
        }).catch(reason => {
          console.log(reason);
          this.requesting = false;
          failed();
        });
      }, 0);
    });
  }

  tabFunction(cm) {
    const cursor = cm.getCursor();
    const line = cm.getLine(cursor.line);
    if (cursor.ch && line[cursor.ch - 1] !== ' ') {
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

  handleChangeLanguage(event) {
    // console.log(this.cm);
    this.options.mode = event.target.value;
    // this.cm.setOption('mode', event.target.value);
    this.setState({language: event.target.value});
  }

  handleChangeModel(event) {
    this.setState({model: event.target.value});
  }

  handleChangeGuess(event, newValue) {
    this.setState({guess: newValue});
  }

  handleChangeLines(event, newValue) {
    this.setState({lines: newValue});
  }

  componentDidMount() {
    const getModelsURL = `${this.props.backend}/get_models`;
    fetch(getModelsURL, {
      mode: 'cors',
      method: 'GET',
      cache: 'no-cache',
    }).then((response) => {
      if (!response.ok) throw Error(response.statusText);
      return response.json();
    }).then(data => {
      console.log(data.data.results);
      this.setState({
        models: data.data.results,
        model: data.data.results[0],
      });
    }).catch(reason => {
      console.log(reason);
    });
  }

  constructor(props: AppProps, context: any) {
    super(props, context);
    this.languages = [
      'python',
      'robotframework',
    ];
    this.cm = null;
    this.state = {
      code: '# Press Tab to toggle the autocomplete list.\n\n',
      language: this.languages[0],
      model: '',
      models: [],
      guess: 3,
      lines: 10,
    };
    this.options = {
      lineNumbers: true,
      styleActiveLine: true,
      matchBrackets: true,
      mode: this.state.language,
      theme: 'material-darker',
      indentWithTabs: true,
      indentUnit: 4,
      extraKeys: {
        'Tab': this.tabFunction.bind(this),
      },
      hintOptions: {hint: this.getHints.bind(this)},
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
                  based language models. We have lots of models for you to
                  choose, the number inside the model name is the number of
                  programs we used as training data.
                </Typography>
                <br/>
                <Typography>
                  The model was designed by BigCoder Team,
                  Nanyang Technological University, Singapore.
                </Typography>
                <br/>
                <Grid container spacing={4}>
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl style={{width: '100%'}}>
                      <InputLabel shrink id="choose-language-label">
                        Choose a Language
                      </InputLabel>
                      <Select
                          labelId="choose-language-label"
                          value={this.state.language}
                          onChange={this.handleChangeLanguage.bind(this)}
                          displayEmpty
                          autoWidth
                      >
                        {this.languages.map((model, index) =>
                            <MenuItem key={index}
                                      value={model}>{model}</MenuItem>,
                        )}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl style={{width: '100%'}}>
                      <InputLabel shrink id="choose-model-label">
                        Choose a Model
                      </InputLabel>
                      <Select
                          labelId="choose-model-label"
                          value={this.state.model}
                          onChange={this.handleChangeModel.bind(this)}
                          displayEmpty
                          autoWidth
                      >
                        {this.state.models.map((model, index) =>
                            <MenuItem key={index}
                                      value={model}>{model}</MenuItem>,
                        )}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <InputLabel shrink id="choose-guess-label">
                      Guess Number
                    </InputLabel>
                    <Slider
                        valueLabelDisplay="auto"
                        step={1} min={1} max={10} marks
                        value={this.state.guess}
                        onChange={this.handleChangeGuess.bind(this)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <InputLabel shrink id="choose-lines-label">
                      Keyword Lines
                    </InputLabel>
                    <Slider
                        valueLabelDisplay="auto"
                        step={1} min={0} max={10} marks
                        value={this.state.lines}
                        onChange={this.handleChangeLines.bind(this)}
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Paper>
          <Paper className="App-paper">
            <CodeMirror className="App-codemirror"
                        value={this.state.code} options={this.options}
                        editorDidMount={editor => { this.cm = editor }}/>
          </Paper>
        </Container>
    );
  }
}

export default App;
