const WeatherService = require("../services/weatherService");
const weatherService = new WeatherService();


class WeatherController {
    constructor(weatherService) {
        this.weatherService = weatherService;
        this.getWeather = this.getWeather.bind(this);
    }

    async getWeather(req, res) {
        const city = req.params.city;
        try {
            const weatherData = await this.weatherService.getWeatherByCity(city);
            res.status(200).json(weatherData);
        } catch (error) {
            res.status(500).json({ error: 'Failed to fetch weather data' });
        }
    }
}

module.exports = new WeatherController(weatherService);