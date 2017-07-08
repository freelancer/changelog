import { h, Component } from 'preact';
import { Router, Route } from 'react-router';
import { createBrowserHistory } from 'history';
import { syncHistoryWithStore } from 'react-router-redux';
import { Provider } from 'react-redux';
import { ThemeProvider } from 'styled-components';
import theme from '../styles/theme/index';
import store from '../store';
import Toolbar from './Toolbar';
import Home from './routes/Home';

const history = syncHistoryWithStore(createBrowserHistory(), store);

export default class App extends Component {
  componentWillMount() {
    // fetch('http://localhost:5000/data')
    //   .then(response => response.json());
  }

  render() {
    return (
      <ThemeProvider theme={theme}>
        <Provider store={store}>
          <Router history={history}>
            <div>
              <Toolbar>
                <h1>What did we do?</h1>
              </Toolbar>
              <Route path="/" component={Home} />
            </div>
          </Router>
        </Provider>
      </ThemeProvider>
    );
  }
}
