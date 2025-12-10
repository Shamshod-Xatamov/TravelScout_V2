import json
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from amadeus import Client, ResponseError

# 1. Amadeusga ulanish
amadeus = Client(
    client_id=settings.AMADEUS_CLIENT_ID,
    client_secret=settings.AMADEUS_CLIENT_SECRET,
    hostname='test'  # Hozircha 'test' rejimdamiz
)


@login_required
def flight_search_page(request):
    """Qidiruv sahifasini (HTML) qaytaradi"""
    return render(request, 'flights/flight_search.html')


@login_required
def flight_search_api(request):
    """Frontenddan kelgan so'rovni Amadeusga yuboradi va natijani JSON qiladi"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)

        # Ma'lumotlarni o'qish
        origin = data.get('from', '').upper()
        destination = data.get('to', '').upper()
        date = data.get('departDate')
        passengers = int(data.get('passengers', 1))

        # Klassni to'g'irlash
        travel_class_map = {
            'economy': 'ECONOMY',
            'premium': 'PREMIUM_ECONOMY',
            'business': 'BUSINESS',
            'first': 'FIRST'
        }
        travel_class = travel_class_map.get(data.get('class', 'economy'), 'ECONOMY')

        if not origin or not destination or not date:
            return JsonResponse({'error': 'Please fill all required fields'}, status=400)

        # 2. HAQIQIY AMADEUS API CHAQIRUVI
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=passengers,
            travelClass=travel_class,
            max=10
        )

        # 3. KELGAN JAVOBNI PARSING QILISH
        results = []
        offers = response.data
        dictionaries = response.result.get('dictionaries', {})

        for offer in offers:
            itinerary = offer['itineraries'][0]
            segment = itinerary['segments'][0]
            carrier_code = segment['carrierCode']
            airline_name = dictionaries.get('carriers', {}).get(carrier_code, carrier_code)

            # Vaqtni olish
            dep_time_raw = segment['departure']['at']  # "2023-12-01T10:00:00"
            arr_time_raw = segment['arrival']['at']

            # Duration (PT5H30M -> 5h 30m ga o'girish qiyin bo'lsa, shunchaki raw olamiz)
            duration_raw = itinerary['duration'].replace('PT', '').lower()

            flight_data = {
                "id": offer['id'],
                "airline": airline_name,
                "flightNumber": f"{carrier_code} {segment['number']}",
                "departure": {
                    "airport": segment['departure']['iataCode'],
                    "city": origin,
                    "time": dep_time_raw.split('T')[1][:5]
                },
                "arrival": {
                    "airport": segment['arrival']['iataCode'],
                    "city": destination,
                    "time": arr_time_raw.split('T')[1][:5]
                },
                "duration": duration_raw,
                "price": float(offer['price']['total']),
                "currency": offer['price']['currency'],
                "stops": len(itinerary['segments']) - 1,
                "class": travel_class.capitalize(),
                "rating": 4.5
            }
            results.append(flight_data)

        return JsonResponse({'status': 'success', 'results': results})

    except ResponseError as error:
        print(f"Amadeus Error: {error}")
        # Xatoni chiroyliroq qaytaramiz
        return JsonResponse({
            'error': 'No flights found. Make sure to use IATA codes (e.g. TAS, JFK, IST).'
        }, status=400)

    except Exception as e:
        print(f"Server Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)