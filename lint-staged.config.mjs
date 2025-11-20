export default {
  "*.py": "npm run format-python",
  "!(*.{js,mjs,cjs,ts})": "prettier --ignore-unknown --write",
  "*.{js,mjs,cjs,ts}": ["eslint --fix"], // (Prettier included in eslint)
};
