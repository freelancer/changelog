import { combineReducers } from 'redux';
import { routerReducer } from 'react-router-redux';
import tagsReducer from './tags';
import filterReducer from './filter';
import eventsReducer from './events';

export default combineReducers({
  routing: routerReducer,
  tags: tagsReducer,
  filter: filterReducer,
  events: eventsReducer,
});

