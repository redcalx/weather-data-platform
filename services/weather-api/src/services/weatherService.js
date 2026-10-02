const apiClient = require('../utils/apiClient');

class WeatherService {
    constructor(apiClientInstance = apiClient) {
        this.apiClient = apiClientInstance;
        this.apiKey = process.env.API_KEY; // Ensure you have your API key in the .env file
    }

    async getWeatherByCity(city) {
        const url = `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${this.apiKey}&units=metric`;
        try {
            const response = await this.apiClient.fetchWeatherData(url);
            return response;
        } catch (error) {
            throw new Error('Error fetching weather data: ' + error.message);
        }
    }
}

module.exports = WeatherService;