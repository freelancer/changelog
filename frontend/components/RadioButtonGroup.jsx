import { h, Component } from 'preact';
import Preact from 'preact-compat';
import PropTypes from 'prop-types';

export default class RadioButtonGroup extends Component {
  static propTypes = {
    children: PropTypes.children.isRequired,
    name: PropTypes.string.isRequired,
  }

  renderChildren() {
    return Preact.Children.map(this.props.children, child => Preact.cloneElement(child, {
      name: this.props.name,
    }));
  }

  render() {
    return (
      <div>{this.renderChildren()}</div>
    );
  }
}
