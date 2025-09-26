export default {
  "!(*.{js,mjs,cjs,ts})": "prettier --ignore-unknown --write",
  "*.{js,mjs,cjs,ts}": ["eslint --fix"], // (Prettier included in eslint)
};
