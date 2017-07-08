export default function (state = [], action) {
  if (action.type === 'TAGS_FETCH_SUCCESS') {
    return action.data;
  }

  return state;
}
