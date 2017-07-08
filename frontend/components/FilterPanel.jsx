import { h, Component } from 'preact';
import { connect } from 'react-redux';
import Panel from './Panel';
import RadioButton from './RadioButton';
import ButtonGroup from './ButtonGroup';
import TagSelect from './TagSelect';
import store from '../store';
import { setFilterTimestamp } from '../actions/filter';

class FilterPanel extends Component {
  render({ onTimestampChange }) {
    return (
      <Panel>
        <h2>Filter</h2>
        <form>
          <label>Timestamp</label>
          <ButtonGroup>
            <RadioButton name="timestamp" value="1h" onChange={() => onTimestampChange(3600)}>1h</RadioButton>
            <RadioButton name="timestamp" value="4h" onChange={() => onTimestampChange(14400)}>4h</RadioButton>
            <RadioButton name="timestamp" value="12h" onChange={() => onTimestampChange(43200)}>12h</RadioButton>
            <RadioButton name="timestamp" value="1w" onChange={() => onTimestampChange(604800)}>1w</RadioButton>
          </ButtonGroup>
          <TagSelect />
        </form>
      </Panel>
    );
  }
}

export default connect((() => ({})), ({
  onTimestampChange: time => store.dispatch(setFilterTimestamp(time)),
}))(FilterPanel);
