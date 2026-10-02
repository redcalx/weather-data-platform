const express = require('express');
const bodyParser = require('body-parser');
const weatherController = require('./controllers/weatherController');


const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());

app.get('/weather/:city', weatherController.getWeather);

if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Server is running on port ${PORT}`);
    });
}

module.exports = app;
