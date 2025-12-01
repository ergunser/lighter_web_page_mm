import requests
import json
import time

BASE_URL = "https://api.lighter.xyz"
# BASE_URL = "https://mainnet.zklighter.elliot.ai" # Trying this one based on search
BASE_URLS = [
    "https://mainnet.zklighter.elliot.ai"
]

PATHS_TO_PROBE = [
    "/orderBooks",
    "/v1/orderBooks",
    "/api/v1/orderBooks",
    "/api/orderBooks",
    "/status",
    "/v1/status"
]

def test_order_books():
    for base_url in BASE_URLS:
        print(f"Testing on {base_url}...")
        for path in PATHS_TO_PROBE:
            print(f"  Probing {path}...")
            try:
                url = f"{base_url}{path}"
                response = requests.get(url, timeout=5)
                print(f"  Status Code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"  Success! Found data at {path}")
                    # If it's the orderBooks endpoint, return it
                    if "orderBooks" in path:
                         print(f"  Found {len(data)} items.")
                         print(f"  Data Type: {type(data)}")
                         if isinstance(data, dict):
                             print(f"  Keys: {data.keys()}")
                             # Try to find the list
                             if "orderBooks" in data:
                                 return base_url, data["orderBooks"][0]
                             elif "order_books" in data:
                                 return base_url, data["order_books"][0]
                             elif "result" in data:
                                 return base_url, data["result"][0]
                             elif "data" in data:
                                 return base_url, data["data"][0]
                         elif isinstance(data, list):
                             if len(data) > 0:
                                return base_url, data[0]
                    # If it's status, just print it
                    else:
                        print("  Status response:", data)
            except Exception as e:
                print(f"  Exception: {e}")
    return None, None

def test_candlesticks(order_book):
    print(f"\nTesting /candlesticks for OrderBook: {order_book}...")
    
    market_id = order_book.get('market_id')
    symbol = order_book.get('symbol')
    
    # Construct URL correctly based on base_url structure
    if "api/v1" not in BASE_URL:
         url = f"{BASE_URL}/api/v1/candlesticks"
    else:
         url = f"{BASE_URL}/candlesticks"

    end_time = int(time.time())
    start_time = end_time - (7 * 24 * 60 * 60) # 7 days ago

    # Use known valid resolution and market_id and time keys
    resolutions = ["1h"]
    # Try with start/end AND count_back, or just end/count_back
    # The error said count_back is not set, so it's required.
    
    param_combinations = []
    
    # Combination 1: start, end, count_back
    param_combinations.append({
        "market_id": market_id,
        "resolution": "1h",
        "start_timestamp": start_time,
        "end_timestamp": end_time,
        "count_back": 168 # 7 days * 24 hours
    })
    
    # Combination 2: end, count_back (no start)
    param_combinations.append({
        "market_id": market_id,
        "resolution": "1h",
        "end_timestamp": end_time,
        "count_back": 168
    })

    print(f"Trying {len(param_combinations)} combinations...")
    
    for params in param_combinations:
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                print(f"SUCCESS! Params: {params}")
                data = response.json()
                print(f"Received data keys: {data.keys() if isinstance(data, dict) else 'list'}")
                if isinstance(data, dict) and "candlesticks" in data:
                     print(f"Found {len(data['candlesticks'])} candles.")
                     if len(data['candlesticks']) > 0:
                         print("Sample Candle:", data['candlesticks'][0])
                     return # Success
            else:
               print(f"Failed with {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    base_url, first_book = test_order_books()
    if first_book and base_url:
        BASE_URL = base_url
        test_candlesticks(first_book)
