import { h, Component } from 'preact';
import Select from 'react-select';
import { connect } from 'react-redux';

class TagSelect extends Component {
  render({ options }) {
    return (
      <div>
        <label htmlFor="tags">Tags</label>
        <Select id="tags" name="tags" multi options={options} />
      </div>
    );
  }
}

function formatTags(data) {
  return data.map(entry => ({
    value: entry.name,
    label: entry.name,
  }));
}

export default connect(state => ({
  options: formatTags(state.tags),
}))(TagSelect);
