const initialState = {
  timestamp: 3600,
};

export default function (state = initialState, action) {
  if (action.type === 'FILTER_TIMESTAMP_SET') {
    return {
      ...state,
      timestamp: action.data,
    };
  }

  return state;
}
