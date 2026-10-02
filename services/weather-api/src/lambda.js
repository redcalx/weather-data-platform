const serverless = require('serverless-http');
const app = require('./index');

module.exports.handler = serverless(app); // Assuming your Express app is exported from app.js