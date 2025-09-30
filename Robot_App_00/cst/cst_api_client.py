import requests
import urllib3

# إخفاء تحذير SSL عند استخدام verify=False على localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_message(session_id: str, message: str) -> str:
    url = "https://localhost:7176/api/Chat/message"
    headers = {"accept": "*/*", "Content-Type": "application/json"}
    payload = {"sessionId": session_id, "message": message}

    try:
        resp = requests.post(url, headers=headers, json=payload, verify=False)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", "")
    except requests.RequestException as e:
        return f"خطأ أثناء الاتصال بالـ API: {e}"


# تجربة
#result = send_message("ef604e99-3f60-42a3-b773-09e2811b3dc3", "اعرض اخر الايميلات")
#print(result)
