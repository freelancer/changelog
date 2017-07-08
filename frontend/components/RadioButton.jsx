import { h, Component } from 'preact';
import PropTypes from 'prop-types';
import styled from 'styled-components';

const ContainerLabel = styled.label`
  display: inline-block;
  background: #bbb;
  border: 1px solid #ccc;
  padding: 4px 8px;
  ${props => props.active && `
    background: white;
    color: black;
  `}
`;

const Radio = styled.input.attrs({
  type: 'radio',
})`
  opacity: 0;
  width: 0;
  height: 0;
`;

export default class RadioButton extends Component {
  static defaultProps = {
    active: false,
    onChange: () => {},
  }

  static propTypes = {
    active: PropTypes.boolean,
    onChange: PropTypes.func,
  }

  constructor(props) {
    super(props);
    this.state = {
      active: props.active,
    };

    this.handleOnChange = this.handleOnChange.bind(this);
  }
  handleOnChange() {
    // Change styling
    this.setState({
      active: !this.state.active,
    });

    this.props.onChange();
  }

  render({ children, ...props }, { active }) {
    return (
      <ContainerLabel active={active}>
        <Radio {...props} onChange={this.handleOnChange} />
        {children}
      </ContainerLabel>
    );
  }
}
