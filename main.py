from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import statistics

app = Flask(__name__)


def get_city_coordinates(city_name):
    """Получаем координаты города через геокодирование API"""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        'name': city_name,
        'count': 1,
        'language': 'ru',
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            city_data = data['results'][0]
            return {
                'lat': city_data['latitude'],
                'lon': city_data['longitude'],
                'name': city_data['name'],
                'country': city_data.get('country', '')
            }
        return None
    except Exception as e:
        print(f"Ошибка геокодирования: {e}")
        return None


def get_historical_weather(lat, lon, days=30):
    """Получаем исторические данные погоды через API"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
        'timezone': 'auto'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None


def analyze_weather_data(weather_data):
    """АНАЛИЗИРУЕМ ВСЕ 30 ДНЕЙ"""
    temps_max = weather_data['daily']['temperature_2m_max']
    temps_min = weather_data['daily']['temperature_2m_min']
    precipitation = weather_data['daily']['precipitation_sum']

    # Анализ всех 30 дней
    avg_temp_all = statistics.mean(temps_max)
    max_temp = max(temps_max)
    min_temp = min(temps_min)

    # Анализ тенденции - сравниваем первую и вторую половину месяца
    half = len(temps_max) // 2
    first_half_avg_max = statistics.mean(temps_max[:half])
    second_half_avg_max = statistics.mean(temps_max[half:])
    first_half_avg_min = statistics.mean(temps_min[:half])
    second_half_avg_min = statistics.mean(temps_min[half:])

    # Определяем тренд
    if second_half_avg_max > first_half_avg_max:
        trend = 'потепление'
        trend_value_max = second_half_avg_max - first_half_avg_max
        trend_value_min = second_half_avg_min - first_half_avg_min
    else:
        trend = 'похолодание'
        trend_value_max = first_half_avg_max - second_half_avg_max
        trend_value_min = first_half_avg_min - second_half_avg_min

    # Прогноз на завтра для максимальной температуры
    last_week_avg_max = statistics.mean(temps_max[-7:])
    forecast_max = last_week_avg_max + (trend_value_max * 0.3)

    # Прогноз на завтра для минимальной температуры
    last_week_avg_min = statistics.mean(temps_min[-7:])
    forecast_min = last_week_avg_min + (trend_value_min * 0.3)

    # Средняя температура на завтра
    forecast_avg = (forecast_max + forecast_min) / 2

    # Прогноз осадков на завтра (на основе последней недели)
    last_week_precip = precipitation[-7:]
    avg_precipitation = statistics.mean(last_week_precip) if last_week_precip else 0
    forecast_precipitation = max(0, avg_precipitation)  # Осадки не могут быть отрицательными

    # Анализ осадков за месяц
    rainy_days = sum(1 for p in precipitation if p > 0)
    total_precipitation = sum(precipitation)

    return {
        'avg_temp_all': round(avg_temp_all, 1),
        'max_temp': round(max_temp, 1),
        'min_temp': round(min_temp, 1),
        'trend': trend,
        'trend_value': round(trend_value_max, 1),
        'forecast_tomorrow_max': round(forecast_max, 1),
        'forecast_tomorrow_min': round(forecast_min, 1),
        'forecast_tomorrow_avg': round(forecast_avg, 1),
        'forecast_precipitation': round(forecast_precipitation, 1),
        'rainy_days': rainy_days,
        'total_precipitation': round(total_precipitation, 1),
        'days_analyzed': len(temps_max)
    }


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/get_weather', methods=['POST'])
def get_weather():
    """API endpoint для получения погоды"""
    city_name = request.json.get('city', '').strip()

    if not city_name:
        return jsonify({'error': 'Введите название города'}), 400

    # 1. Получаем координаты города
    coords = get_city_coordinates(city_name)
    if not coords:
        return jsonify({'error': f'Город "{city_name}" не найден'}), 404

    # 2. Получаем исторические данные погоды
    weather_data = get_historical_weather(coords['lat'], coords['lon'])

    if not weather_data or 'daily' not in weather_data:
        return jsonify({'error': 'Не удалось получить данные о погоде'}), 500

    # 3. АНАЛИЗИРУЕМ ДАННЫЕ
    analysis = analyze_weather_data(weather_data)

    # 4. Форматируем ответ
    result = {
        'city_name': coords['name'],
        'country': coords['country'],
        'weather_data': [],
        'analysis': analysis
    }

    # Собираем данные по дням
    for i in range(len(weather_data['daily']['time'])):
        day_data = {
            'date': weather_data['daily']['time'][i],
            'temp_max': weather_data['daily']['temperature_2m_max'][i],
            'temp_min': weather_data['daily']['temperature_2m_min'][i],
            'precipitation': weather_data['daily']['precipitation_sum'][i]
        }
        result['weather_data'].append(day_data)

    return jsonify(result)


if __name__ == '__main__':
    print("🚀 Запускаем Flask сервер...")
    print("📧 Открой в браузере: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)