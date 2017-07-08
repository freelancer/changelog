export default function (state = {}, action) {
  if (action.type === 'EVENTS_FETCH_SUCCESS') {
    return action.data;
  }

  return state;
}
