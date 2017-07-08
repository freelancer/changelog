import { combineEpics } from 'redux-observable';
import { Observable } from 'rxjs/Observable';

// Mock epic
const fooEpic = () => Observable.empty();

export default combineEpics(fooEpic);
