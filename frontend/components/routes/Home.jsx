import { h, Component } from 'preact';
import styled from 'styled-components';
import FilterPanel from '../FilterPanel';
import DataTable from '../DataTable';
import { tagsFetched } from '../../actions/tags';
import { eventsFetched } from '../../actions/events';
import store from '../../store';

const Container = styled.div`
  padding: 16px;
`;

export default class Home extends Component {
  componentWillMount() {
    fetch('http://127.0.0.1:5000/api/tags')
      .then(response => response.json())
      .then((data) => {
        store.dispatch(tagsFetched(data));
      });

    fetch('http://127.0.0.1:5000/api/events?hours_ago=720&until=-1')
      .then(response => response.json())
      .then((data) => {
        store.dispatch(eventsFetched(data));
      });
  }

  render() {
    return (
      <Container>
        <FilterPanel />
        <DataTable />
      </Container>
    );
  }
}
