import requests, json
from concurrent.futures import ThreadPoolExecutor, as_completed

# 🔑 Daftar API JWT (3 endpoint berbeda)
API_URLS = [
    "https://jwt-1-zx-ff.vercel.app/token?uid={}&password={}",
    "https://jwt-2-zx-ff.vercel.app/token?uid={}&password={}"
]

def fetch_token(uid, password):
    """Coba ambil token dari daftar API sampai dapat"""
    for api in API_URLS:
        try:
            url = api.format(uid, password)
            response = requests.get(url).json()   # ❌ tanpa timeout
            if 'token' in response:
                return response
        except Exception as e:
            print(f"[WARN] API gagal: {api} -> {e}")
            continue
    return None

def process_account(account):
    """Proses satu akun"""
    try:
        response = fetch_token(account['uid'], account['password'])
        if response and 'token' in response:
            region_code = response.get('notiRegion', '').upper()
            if region_code == 'IND':
                region = 'IND'
            elif region_code in {'BR', 'US', 'SAC', 'NA'}:
                region = 'BR'
            else:
                region = 'BD'
            
            return {
                "uid": account['uid'],
                "token": response['token'],
                "region": region
            }
        else:
            return {"uid": account['uid'], "error": "no token"}
    except Exception as e:
        return {"uid": account['uid'], "error": str(e)}

def generate_tokens(input_file, max_workers=5):
    try:
        with open(input_file) as f:
            accounts = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: '{input_file}' is not valid JSON or is empty.")
        return
    
    result = {'IND': [], 'BR': [], 'BD': []}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_account, acc): acc for acc in accounts}
        for future in as_completed(futures):
            data = future.result()
            if "error" in data:
                print(f"❌ FAIL({data['uid']}) -> {data['error']}")
            else:
                print(f"✅ OK({data['uid']}) -> {data['region']}")
                result[data['region']].append({
                    "uid": data['uid'],
                    "token": data['token']
                })

    # Save hasil per region
    for region, tokens in result.items():
        if tokens:
            filename = f"token_{region.lower()}.json"
            with open(filename, "w") as f:
                json.dump(tokens, f, indent=4)
            print(f"💾 Saved {len(tokens)} tokens to {filename}")

# 🚀 Jalankan
generate_tokens("accounts.json", max_workers=20)
