const axios = require ('axios');

module.exports = {
    async fetchWeatherData(url) {
        try{
            const response = await axios.get(url);
            return response.data;
        } catch (error) {
            console.error('Error fetching weather data:', error.message);
            throw new Error('Failed to fetch weather data');
        }
    }
}