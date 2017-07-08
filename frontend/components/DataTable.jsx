import { h, Component } from 'preact';
import { connect } from 'react-redux';
import ReactTable from 'react-table';
import * as moment from 'moment';

class DataTable extends Component {
  componentWillMount() {
    this.columns = [{
      accessor: 'start_time',
      Header: 'Start Time',
      Cell: cell => moment.unix(cell.row.start_time).format('YYYY-MM-DD HH:mm:ss Z'),
      filterMethod: (filter, row) => {
        console.log(filter.value);
        const timeFilter = moment().subtract(filter.value, 'ms');
        return moment.unix(row[filter.id]).isAfter(timeFilter);
      },
    }, {
      accessor: 'end_time',
      Header: 'End Time',
      Cell: cell => moment.unix(cell.row.end_time).format('YYYY-MM-DD HH:mm:ss Z'),
    }, {
      accessor: 'source',
      Header: 'Source',
    }, {
      id: 'tags',
      Header: 'Tags',
      accessor: row => row.tags.map(tag => tag.name).join(', '),
    }, {
      accessor: 'description',
      Header: 'Description',
    }];
  }


  render({ rows, filter }) {
    return (
      <ReactTable
        data={rows}
        columns={this.columns}
        sortable={false}
        filters={[{
          start_time: filter.timestamp,
        }]}
      />
    );
  }
}

export default connect(state => ({
  rows: Object.keys(state.events).map(key => ({ id: key, ...state.events[key] })),
  filter: state.filter,
}))(DataTable);
