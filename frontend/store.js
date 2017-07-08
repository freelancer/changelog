import { compose, createStore, applyMiddleware } from 'redux';
import { persistStore, autoRehydrate } from 'redux-persist';
import localForage from 'localforage';
import { composeWithDevTools } from 'redux-devtools-extension';
import { createEpicMiddleware } from 'redux-observable';
import reducers from './reducers/index';
import epics from './epics/index';

const store = createStore(
  reducers,
  composeWithDevTools(
    applyMiddleware(createEpicMiddleware(epics)),
  ),
  compose(autoRehydrate()),
);

export default store;

persistStore(store, { storage: localForage });
