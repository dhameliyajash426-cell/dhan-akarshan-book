#!/usr/bin/env python3
"""
Cashfree Payment Gateway Server for 'Dhan Akarshan Rahasya' eBook
==================================================================
Handles:
  - Serving the landing page (index.html)
  - Order creation on Cashfree PG API (POST /api/create-order)
  - Payment verification & eBook link delivery (GET /verify?order_id=...)
  - API status check (GET /api/check-order-status)
  - Admin preview of success page (GET /preview-success)
  - Customer order log persistence (orders.json)
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import time
import random
import datetime

# --- Load .env if present (Zero-dependency parser) ---
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

# --- Configuration ---
PORT = int(os.environ.get('PORT', 8000))
CASHFREE_APP_ID = os.environ.get('CASHFREE_APP_ID', '1342214ec78d96bbcb1828c07074122431')
CASHFREE_SECRET_KEY = os.environ.get('CASHFREE_SECRET_KEY', '')
CASHFREE_API_VERSION = os.environ.get('CASHFREE_API_VERSION', '2023-08-01')
CASHFREE_BASE_URL = os.environ.get('CASHFREE_BASE_URL', 'https://api.cashfree.com/pg')

PRODUCT_NAME = 'धन आकर्षण रहस्य (The Secret to Attract Wealth)'
PRODUCT_LINK = os.environ.get(
    'PRODUCT_LINK',
    'https://drive.google.com/drive/folders/1oZwLB5KYi3NjMGEDx-5dLF9fKt_pstpe?usp=sharing'
)
DEFAULT_AMOUNT = float(os.environ.get('ORDER_AMOUNT', '299.00'))
CURRENCY = 'INR'
SUPPORT_WHATSAPP = '919910124156'
BASE_URL = os.environ.get('BASE_URL', '').rstrip('/')
ORDERS_DB_FILE = os.path.join(os.path.dirname(__file__), 'orders.json')

# --- Helper: Save Order to orders.json ---
def log_successful_order(order_data):
    try:
        orders = []
        if os.path.exists(ORDERS_DB_FILE):
            with open(ORDERS_DB_FILE, 'r', encoding='utf-8') as f:
                try:
                    orders = json.load(f)
                except Exception:
                    orders = []
        
        # Avoid duplicate logs for same order_id
        for o in orders:
            if o.get('order_id') == order_data.get('order_id'):
                return
        
        orders.append(order_data)
        with open(ORDERS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        print(f"[ORDER LOGGED] Saved order {order_data.get('order_id')} to orders.json")
    except Exception as e:
        print(f"[ORDER LOG ERROR] {e}")


# --- HTML Templates ---
def render_success_page(order_id, customer_name, customer_email, amount, order_status):
    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Payment Successful | धन आकर्षण रहस्य eBook</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: radial-gradient(circle at 50% 10%, #201a14 0%, #0d0b09 100%);
      color: #fdfaf4;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px 16px;
    }}
    .card {{
      background: rgba(22, 18, 14, 0.95);
      border: 1px solid rgba(212, 175, 55, 0.45);
      border-radius: 20px;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 35px rgba(212, 175, 55, 0.2);
      max-width: 540px;
      width: 100%;
      padding: 36px 28px;
      text-align: center;
      animation: fadeIn 0.4s ease-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(15px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .badge-icon {{
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: linear-gradient(135deg, #18522e 0%, #22c55e 100%);
      border: 3px solid rgba(110, 231, 183, 0.5);
      box-shadow: 0 0 30px rgba(34, 197, 94, 0.4);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 34px;
      margin-bottom: 20px;
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.05); }}
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      color: #fcedcf;
      margin-bottom: 6px;
      line-height: 1.3;
    }}
    .tagline {{
      font-size: 14px;
      color: #c7b69c;
      margin-bottom: 24px;
    }}
    .order-box {{
      background: rgba(0, 0, 0, 0.45);
      border: 1px solid rgba(212, 175, 55, 0.25);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 24px;
      text-align: left;
      font-size: 13px;
    }}
    .order-row {{
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
    }}
    .order-row:last-child {{ border-bottom: none; }}
    .order-label {{ color: #a89880; }}
    .order-val {{ color: #f5d47a; font-weight: 600; word-break: break-all; }}
    
    .download-card {{
      background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
      border: 2px dashed rgba(212, 175, 55, 0.5);
      border-radius: 14px;
      padding: 24px 20px;
      margin-bottom: 24px;
    }}
    .download-title {{
      font-size: 16px;
      font-weight: 700;
      color: #fcedcf;
      margin-bottom: 8px;
    }}
    .download-desc {{
      font-size: 13px;
      color: #b5a489;
      margin-bottom: 18px;
      line-height: 1.5;
    }}
    .btn-download {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 100%;
      background: linear-gradient(135deg, #f5d47a 0%, #d4af37 50%, #b8860b 100%);
      color: #120e09;
      font-size: 17px;
      font-weight: 800;
      padding: 16px 24px;
      border-radius: 12px;
      text-decoration: none;
      box-shadow: 0 6px 25px rgba(212, 175, 55, 0.45);
      transition: all 0.25s;
    }}
    .btn-download:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 30px rgba(212, 175, 55, 0.65);
      filter: brightness(1.07);
    }}
    .instructions {{
      background: rgba(255, 255, 255, 0.03);
      border-radius: 10px;
      padding: 14px 16px;
      font-size: 12px;
      color: #9f8f78;
      text-align: left;
      line-height: 1.6;
      margin-bottom: 20px;
    }}
    .instructions strong {{ color: #e5d5be; }}
    .whatsapp-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #25d366;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid rgba(37, 211, 102, 0.3);
      background: rgba(37, 211, 102, 0.08);
      transition: all 0.2s;
    }}
    .whatsapp-btn:hover {{
      background: rgba(37, 211, 102, 0.18);
    }}
    .home-link {{
      display: block;
      margin-top: 16px;
      font-size: 13px;
      color: #7b6c56;
      text-decoration: none;
    }}
    .home-link:hover {{ color: #d4af37; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge-icon">✓</div>
    <h1>भुगतान सफल रहा! 🎉</h1>
    <p class="tagline">Payment Verified • धन आकर्षण रहस्य eBook</p>

    <div class="order-box">
      <div class="order-row">
        <span class="order-label">Order ID:</span>
        <span class="order-val">{order_id}</span>
      </div>
      <div class="order-row">
        <span class="order-label">Customer Name:</span>
        <span class="order-val">{customer_name or 'Valued Customer'}</span>
      </div>
      <div class="order-row">
        <span class="order-label">Email ID:</span>
        <span class="order-val">{customer_email or 'Registered'}</span>
      </div>
      <div class="order-row">
        <span class="order-label">Amount Paid:</span>
        <span class="order-val">₹{amount} (Paid via Cashfree)</span>
      </div>
      <div class="order-row">
        <span class="order-label">Status:</span>
        <span class="order-val" style="color: #6ee7b7;">✅ {order_status}</span>
      </div>
    </div>

    <div class="download-card">
      <div class="download-title">📥 आपकी ई-बुक डाउनलोड के लिए तैयार है</div>
      <p class="download-desc">
        नीचे दिए गए बटन पर क्लिक करके Google Drive फोल्डर खोलें। इसमें संपूर्ण 84-पृष्ठ की PDF गाइड, दैनिक अभ्यास और धन आकर्षण मंत्र शामिल हैं।
      </p>
      <a href="{PRODUCT_LINK}" target="_blank" rel="noopener noreferrer" class="btn-download">
        <span>🚀 Google Drive पर eBook खोलें व डाउनलोड करें</span>
        <span>➔</span>
      </a>
    </div>

    <div class="instructions">
      <strong>महत्वपूर्ण सूचना (Helpful Instructions):</strong><br>
      • कृपया इस Google Drive लिंक को अपने ब्राउज़र में बुकमार्क (Bookmark) कर लें ताकि आप कभी भी इसे पढ़ सकें।<br>
      • PDF को अपने फ़ोन या लैपटॉप पर डाउनलोड करके सुरक्षित रख लें।<br>
      • किसी भी सहायता के लिए आप नीचे व्हाट्सएप पर हमसे संपर्क कर सकते हैं।
    </div>

    <a href="https://wa.me/{SUPPORT_WHATSAPP}?text={urllib.parse.quote(f'Hi, I purchased Dhan Akarshan Rahasya. Order ID: {order_id}')}" target="_blank" rel="noopener noreferrer" class="whatsapp-btn">
      <span>💬 WhatsApp Support पर संपर्क करें</span>
    </a>

    <a href="/" class="home-link">← वापस होमपेज पर जाएं (Back to Homepage)</a>
  </div>
</body>
</html>
"""


def render_failed_page(order_id, status, message):
    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Payment Status | धन आकर्षण रहस्य</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: radial-gradient(circle at 50% 10%, #201a14 0%, #0d0b09 100%);
      color: #fdfaf4;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px 16px;
    }}
    .card {{
      background: rgba(22, 18, 14, 0.95);
      border: 1px solid rgba(248, 113, 113, 0.35);
      border-radius: 20px;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9);
      max-width: 500px;
      width: 100%;
      padding: 36px 28px;
      text-align: center;
    }}
    .badge-icon {{
      width: 68px;
      height: 68px;
      border-radius: 50%;
      background: rgba(239, 68, 68, 0.15);
      border: 2px solid rgba(239, 68, 68, 0.4);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 30px;
      margin-bottom: 20px;
      color: #f87171;
    }}
    h1 {{
      font-size: 24px;
      font-weight: 800;
      color: #fee2e2;
      margin-bottom: 8px;
    }}
    .tagline {{
      font-size: 13px;
      color: #b5a489;
      margin-bottom: 20px;
    }}
    .msg-box {{
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      padding: 16px;
      font-size: 13px;
      color: #ded0b7;
      line-height: 1.5;
      margin-bottom: 24px;
    }}
    .btn-retry {{
      display: inline-block;
      width: 100%;
      background: linear-gradient(135deg, #f5d47a 0%, #d4af37 100%);
      color: #120e09;
      font-size: 15px;
      font-weight: 700;
      padding: 14px 20px;
      border-radius: 10px;
      text-decoration: none;
      margin-bottom: 12px;
    }}
    .whatsapp-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      color: #25d366;
      font-size: 13px;
      text-decoration: none;
      padding: 8px 14px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge-icon">!</div>
    <h1>भुगतान अधूरा या लंबित है</h1>
    <p class="tagline">Payment Incomplete / Pending</p>

    <div class="msg-box">
      <strong>Order ID:</strong> {order_id}<br>
      <strong>Status:</strong> {status}<br><br>
      {message}<br><br>
      <small style="color: #9f8f78;">
        यदि आपके बैंक से पैसे कट चुके हैं, तो कृपया 5-10 मिनट प्रतीक्षा करें या सहायता के लिए व्हाट्सएप पर मैसेज भेजें।
      </small>
    </div>

    <a href="/?buy=1" class="btn-retry">पुनः प्रयास करें (Retry Payment)</a>
    <br>
    <a href="https://wa.me/{SUPPORT_WHATSAPP}?text={urllib.parse.quote(f'Hi, my payment is incomplete. Order ID: {order_id}')}" target="_blank" rel="noopener noreferrer" class="whatsapp-btn">
      💬 WhatsApp Support से बात करें
    </a>
  </div>
</body>
</html>
"""


# --- Request Handler ---
class CashfreeServerHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        # Clean timestamped console log
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]} {args[1]} {args[2]}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Root / Landing Page
        if path == '/' or path == '/index.html' or path == '/dhan_letsdfy_in-digital-only.html':
            self.serve_landing_page()
            return

        # 2. Checkout Redirect to Landing Page with Modal Auto-open
        if path.startswith('/checkout'):
            self.send_response(302)
            self.send_header('Location', '/?buy=1')
            self.end_headers()
            return

        # 3. Payment Return & Verification: /verify?order_id=...
        if path == '/verify':
            order_id = query.get('order_id', [None])[0]
            if not order_id:
                self.send_html_response(render_failed_page('N/A', 'MISSING_ORDER_ID', 'कोई ऑर्डर आईडी प्राप्त नहीं हुआ।'), 400)
                return
            self.verify_order_and_serve(order_id)
            return

        # 4. API check status endpoint: /api/order or /api/check-order-status
        if path == '/api/order' or path == '/api/check-order-status':
            order_id = query.get('order_id', [None])[0]
            if not order_id:
                self.send_json_response({'error': 'Missing order_id'}, 400)
                return
            status_data = self.fetch_cashfree_order(order_id)
            is_paid = status_data.get('order_status') == 'PAID'
            response = {
                'success': True,
                'order_id': order_id,
                'order_status': status_data.get('order_status'),
                'is_paid': is_paid,
                'order_amount': status_data.get('order_amount'),
                'customer_details': status_data.get('customer_details'),
                'product_link': PRODUCT_LINK if is_paid else None
            }
            self.send_json_response(response)
            return

        # 5. Admin Preview of Success Page: /preview-success
        if path == '/preview-success':
            html = render_success_page(
                order_id='DEMO_ORDER_PREVIEW_123',
                customer_name='Demo Customer (परीक्षण ग्राहक)',
                customer_email='customer@example.com',
                amount=DEFAULT_AMOUNT,
                order_status='PAID'
            )
            self.send_html_response(html)
            return

        # 6. Admin Order Records: /orders (simple JSON listing of purchases)
        if path == '/orders':
            if os.path.exists(ORDERS_DB_FILE):
                with open(ORDERS_DB_FILE, 'r', encoding='utf-8') as f:
                    self.send_html_response(f"<pre style='background:#111;color:#eee;padding:20px;font-family:monospace;'>{f.read()}</pre>")
            else:
                self.send_html_response("<pre style='background:#111;color:#eee;padding:20px;'>No orders logged yet.</pre>")
            return

        # Clean policy routes
        clean_routes = {
            '/contact': 'contact.html',
            '/terms': 'terms.html',
            '/privacy': 'privacy.html',
            '/refund': 'refund.html',
            '/license': 'license.html'
        }
        if path in clean_routes and os.path.exists(clean_routes[path]):
            with open(clean_routes[path], 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # Fallback to standard file serving
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Create Order API: /api/order and /api/create-order
        if path == '/api/order' or path == '/api/create-order':
            self.handle_create_order()
            return

        self.send_json_response({'error': 'Not Found'}, 404)

    def serve_landing_page(self):
        target = 'index.html' if os.path.exists('index.html') else 'dhan_letsdfy_in-digital-only.html'
        try:
            with open(target, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_create_order(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body) if body else {}

            name = data.get('customer_name', '').strip() or 'Guest Customer'
            email = data.get('customer_email', '').strip() or 'customer@example.com'
            phone = str(data.get('customer_phone', '')).strip().replace('+', '')[-10:]
            if not phone or len(phone) < 10:
                phone = '9999999999'
            amount = float(data.get('amount', DEFAULT_AMOUNT))

            # Generate Unique Order ID
            order_id = f"order_{int(time.time())}_{random.randint(100, 999)}"

            # Compute Return URL
            # Cashfree Production strictly enforces HTTPS return_url
            return_url = self.compute_return_url(order_id)

            payload = {
                'order_id': order_id,
                'order_amount': amount,
                'order_currency': CURRENCY,
                'customer_details': {
                    'customer_id': f"cust_{phone}_{int(time.time())}",
                    'customer_name': name,
                    'customer_email': email,
                    'customer_phone': phone
                },
                'order_meta': {
                    'return_url': return_url
                },
                'order_note': f"Ebook: {PRODUCT_NAME}"
            }

            headers = {
                'Content-Type': 'application/json',
                'x-client-id': CASHFREE_APP_ID,
                'x-client-secret': CASHFREE_SECRET_KEY,
                'x-api-version': CASHFREE_API_VERSION
            }

            url = f"{CASHFREE_BASE_URL}/orders"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                payment_session_id = resp_data.get('payment_session_id')
                
                print(f"[ORDER CREATED] ID: {order_id} | Session: {payment_session_id[:20]}... | Amount: ₹{amount}")
                self.send_json_response({
                    'success': True,
                    'order_id': order_id,
                    'payment_session_id': payment_session_id,
                    'order_status': resp_data.get('order_status')
                })

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            print(f"[CASHFREE API ERROR] HTTP {e.code}: {err_body}")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get('message', err_body)
            except Exception:
                msg = err_body
            self.send_json_response({'success': False, 'error': msg}, e.code)
        except Exception as e:
            print(f"[INTERNAL ERROR] {e}")
            self.send_json_response({'success': False, 'error': str(e)}, 500)

    def compute_return_url(self, order_id):
        # 1. Configured BASE_URL (from .env or environment)
        if BASE_URL and BASE_URL.startswith('https://'):
            return f"{BASE_URL}/verify?order_id={{{order_id}}}"

        # 2. Check X-Forwarded-Proto & Host (Reverse proxy / Cloudflare / Tunnel)
        host = self.headers.get('Host', '')
        proto = self.headers.get('X-Forwarded-Proto', 'https').split(',')[0].strip()

        if host and not host.startswith('localhost') and not host.startswith('127.0.0.1'):
            return f"{proto}://{host}/verify?order_id={{{order_id}}}"

        # 3. Default fallback for Cashfree production mode (requires https://)
        # In live deployment on user's domain, setting BASE_URL in .env will override this.
        return f"https://dhan.letsdfy.in/verify?order_id={{{order_id}}}"

    def fetch_cashfree_order(self, order_id):
        url = f"{CASHFREE_BASE_URL}/orders/{order_id}"
        headers = {
            'x-client-id': CASHFREE_APP_ID,
            'x-client-secret': CASHFREE_SECRET_KEY,
            'x-api-version': CASHFREE_API_VERSION
        }
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            print(f"[CASHFREE FETCH ERROR] HTTP {e.code}: {err_body}")
            return {'error': True, 'order_status': 'NOT_FOUND', 'message': err_body}
        except Exception as e:
            print(f"[FETCH ERROR] {e}")
            return {'error': True, 'order_status': 'ERROR', 'message': str(e)}

    def verify_order_and_serve(self, order_id):
        order_info = self.fetch_cashfree_order(order_id)
        status = order_info.get('order_status', 'UNKNOWN')
        customer = order_info.get('customer_details', {}) or {}
        amount = order_info.get('order_amount', DEFAULT_AMOUNT)
        name = customer.get('customer_name', '')
        email = customer.get('customer_email', '')
        phone = customer.get('customer_phone', '')

        print(f"[PAYMENT VERIFY] Order ID: {order_id} | Status: {status} | Customer: {name} ({email})")

        if status == 'PAID':
            # Save to orders database
            log_successful_order({
                'order_id': order_id,
                'amount': amount,
                'currency': CURRENCY,
                'status': 'PAID',
                'customer_name': name,
                'customer_email': email,
                'customer_phone': phone,
                'timestamp': datetime.datetime.now().isoformat(),
                'product_link': PRODUCT_LINK
            })

            html = render_success_page(
                order_id=order_id,
                customer_name=name,
                customer_email=email,
                amount=amount,
                order_status=status
            )
            self.send_html_response(html)
        else:
            msg = 'आपका भुगतान अभी तक पूर्ण नहीं हुआ है। यदि आपके खाते से पैसे कट चुके हैं, तो कृपया कुछ देर प्रतीक्षा करें।'
            html = render_failed_page(order_id, status, msg)
            self.send_html_response(html, 400 if status != 'ACTIVE' else 200)

    def send_json_response(self, data, status_code=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_html_response(self, html_str, status_code=200):
        body = html_str.encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CashfreeServerHandler) as httpd:
        print("=" * 60)
        print(f"🚀 Dhan Akarshan Rahasya Cashfree Server RUNNING")
        print(f"👉 Local URL:     http://localhost:{PORT}")
        print(f"👉 Success Demo:  http://localhost:{PORT}/preview-success")
        print(f"👉 Cashfree Mode: PRODUCTION (Active)")
        print(f"👉 Product Link:  {PRODUCT_LINK}")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()


if __name__ == '__main__':
    run_server()
