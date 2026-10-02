jest.mock('axios');
const request = require('supertest');
const app = require('../index'); 
const axios = require('axios');

axios.get.mockResolvedValue({ data: { weather: [{}] } });

describe('GET /weather/:city', () => {
    it('should return weather information for a valid city', async () => {
        const res = await request(app).get('/weather/Belo%20Horizonte');
        expect(res.statusCode).toBe(200);
        expect(res.body).toHaveProperty('weather');
    })

    it('should return 404 for an invalid city', async () => {
        const res = await request(app).get('/weather/InvalidCity');
        expect(res.statusCode).toBe(404);
    })
})