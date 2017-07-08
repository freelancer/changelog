import { injectGlobal } from 'styled-components';

/* TODO: Bug here on no-unused-expressions */
/* eslint-disable */
injectGlobal`
  @import url('https://fonts.googleapis.com/css?family=Roboto:400,400i,700');

  /* stylelint-disable selector-no-type, selector-no-universal */
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  body {
    font-family: 'Roboto', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    line-height: 1.3;
    margin: 0;
  }

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    /* Normalize all font-size to the body text size. */
    font-size: 1rem;
    font-weight: normal;
    margin-bottom: 0;
    margin-top: 0;
  }

  p {
    margin-bottom: 0;
    margin-top: 0;
  }

  a {
    color: inherit;
    cursor: pointer;
    text-decoration: none;
  }

  ul,
  ol {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  input,
  textarea,
  select,
  button {
    font-family: inherit;
  }

  /**
   * This standardises the color of input placeholder text.
   * This selector is intentional to bump up the specificity by 10 in order
   * to make it work on IE (IE has no concept of placeholders as pseudo elements
   * so it inherits the placeholder color from the input color).
   */
  html:not(:empty) ::placeholder {
    color: inherit;
    opacity: 1;
  }
`;
/* eslint-enable */
