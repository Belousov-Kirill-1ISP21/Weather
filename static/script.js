async function getWeather() {
    const cityInput = document.getElementById('cityInput').value.trim();
    const button = document.getElementById('getWeatherBtn');
    
    if (!cityInput) {
        showError('Введите название города');
        return;
    }

    showLoading();
    button.disabled = true;

    try {
        const response = await fetch('/get_weather', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ city: cityInput })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Произошла ошибка');
        }

        displayWeather(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
        button.disabled = false;
    }
}

function displayWeather(data) {
    document.getElementById('cityName').textContent = 
        `Погода в ${data.city_name}, ${data.country}`;
    
    const tableBody = document.getElementById('weatherBody');
    tableBody.innerHTML = '';
    
    // Отображаем данные
    data.weather_data.forEach(day => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${day.date}</td>
            <td>${day.temp_max.toFixed(1)}°C</td>
            <td>${day.temp_min.toFixed(1)}°C</td>
            <td>${day.precipitation} мм</td>
        `;
        tableBody.appendChild(row);
    });
    
    // Отображаем анализ и прогноз
    const analysis = data.analysis;
    const forecastDiv = document.querySelector('.forecast');
    forecastDiv.innerHTML = `
        <h3>📊 Прогноз на завтра</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0;">
            <div>
                <p><strong>Максимальная:</strong> ${analysis.forecast_tomorrow_max}°C</p>
                <p><strong>Минимальная:</strong> ${analysis.forecast_tomorrow_min}°C</p>
            </div>
            <div>
                <p><strong>Средняя:</strong> ${analysis.forecast_tomorrow_avg}°C</p>
                <p><strong>Осадки:</strong> ${analysis.forecast_precipitation} мм</p>
            </div>
        </div>
        <div style="border-top: 1px solid #ccc; padding-top: 10px; margin-top: 10px;">
            <p><strong>Анализ за ${analysis.days_analyzed} дней:</strong> 
            средняя ${analysis.avg_temp_all}°C, тенденция - ${analysis.trend}</p>
        </div>
    `;
    
    document.getElementById('weatherResult').classList.remove('hidden');
}

// Остальные функции без изменений...
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('weatherResult').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    document.getElementById('error').textContent = `❌ ${message}`;
    document.getElementById('error').classList.remove('hidden');
    document.getElementById('weatherResult').classList.add('hidden');
}

document.getElementById('cityInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        getWeather();
    }
});