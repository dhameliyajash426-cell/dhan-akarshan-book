# Dhan Akarshan Rahasya (धन आकर्षण रहस्य) — Cashfree Payment Integration

ई-बुक लैंडिंग पेज के लिए **Cashfree Payment Gateway** का पूर्ण इंटीग्रेशन।

---

## 🌟 फीचर्स (Features)

1. **ऑल-इन-वन लैंडिंग पेज (`index.html`)**:
   - पेज पर मौजूद सभी 16+ **"Get Digital PDF at ₹299"** बटनों पर कैशफ्री का चेकआउट मोडल (Modal) कनेक्टेड है।
   - यूजर का नाम, ईमेल आईडी और 10-अंकों का व्हाट्सएप नंबर प्राप्त करता है।
   - मोबाइल और डेस्कटॉप दोनों के लिए 100% रिस्पॉन्सिव।

2. **सुरक्षित बैकएंड (Secure Backend - `server.py`)**:
   - आपकी **Cashfree App ID** और **Production Secret Key** सुरक्षित रूप से बैकएंड पर रखी गई है (क्लाइंट-साइड पर कभी एक्सपोज़ नहीं होती)।
   - कैशफ्री v3 REST API (`2023-08-01`) के माध्यम से ऑर्डर जनरेट करता है।

3. **पेमेंट वेरिफिकेशन (Payment Verification - `/verify`)**:
   - कस्टमर के भुगतान करने के बाद कैशफ्री बैकएंड पर `order_id` भेजता है।
   - सर्वर कैशफ्री API से रियल-टाइम जांच करता है कि `order_status === "PAID"` है या नहीं।
   - **पेमेंट वेरिफाई होने पर ही** कस्टमर को ई-बुक का गूगल ड्राइव लिंक प्राप्त होता है:
     `https://drive.google.com/drive/folders/1oZwLB5KYi3NjMGEDx-5dLF9fKt_pstpe?usp=sharing`

4. **ऑर्डर डेटाबेस (`orders.json`)**:
   - प्रत्येक सफल भुगतान का विवरण (Order ID, Name, Email, Phone, Amount, Date & Time) `orders.json` में ऑटोमैटिक सुरक्षित सेव हो जाता है।

5. **मल्टी-प्लेटफ़ॉर्म सपोर्ट (Deploy Anywhere)**:
   - **Python** (`server.py`): बिना किसी अतिरिक्त लाइब्रेरी के सीधे चलता है।
   - **Vercel** (`vercel.json` + `api/`): 1-क्लिक में फ्री होस्टिंग और कस्टम डोमेन।
   - **Node.js** (`server.js`): Render, Railway, VPS आदि के लिए।
   - **PHP / cPanel** (`api/create-order.php` और `verify.php`): Hostinger, GoDaddy या अन्य cPanel होस्टिंग के लिए।

---

## 🚀 लोकल कंप्यूटर पर कैसे चलाएं (How to Run Locally)

1. टर्मिनल खोलें और प्रोजेक्ट फ़ोल्डर में जाएं:
   ```bash
   cd "/Users/dhameliyajash/Desktop/money book"
   ```

2. सर्वर स्टार्ट करें:
   ```bash
   python3 server.py
   ```

3. ब्राउज़र में खोलें:
   - **लैंडिंग पेज:** [http://localhost:8000](http://localhost:8000)
   - **सक्सेस पेज प्रीव्यू:** [http://localhost:8000/preview-success](http://localhost:8000/preview-success)
   - **ऑर्डर रिकॉर्ड्स:** [http://localhost:8000/orders](http://localhost:8000/orders)

---

## ⚙️ क्रेडेंशियल्स व सेटिंग्स (`.env`)

फ़ाइल `.env` में निम्नलिखित जानकारी सेट है:

```env
# Cashfree API Credentials
CASHFREE_APP_ID=1342214ec78d96bbcb1828c07074122431
CASHFREE_SECRET_KEY=your_cashfree_secret_key_here
CASHFREE_API_VERSION=2023-08-01

# Product Details
ORDER_AMOUNT=299.00
PRODUCT_LINK=https://drive.google.com/drive/folders/1oZwLB5KYi3NjMGEDx-5dLF9fKt_pstpe?usp=sharing
SUPPORT_WHATSAPP=919910124156

# Live Domain (लाइव करने पर अपना डोमेन यहाँ डालें)
BASE_URL=https://dhan.letsdfy.in
```

---

## 🌐 वेबसाइट लाइव कैसे करें (Deployment Guide)

### तरीका 1: Vercel पर (अनुशंसित - सबसे आसान और तेज़)
1. प्रोजेक्ट को GitHub रिपॉजिटरी में पुश करें या सीधे [vercel.com](https://vercel.com) पर फ़ोल्डर डिप्लॉय करें।
2. फ़ाइल `vercel.json` और `api/` पहले से तैयार हैं।
3. Vercel Dashboard में **Settings > Environment Variables** में जाकर `.env` वाली वैल्यूज जोड़ें।
4. आपका कस्टम डोमेन (जैसे `dhan.letsdfy.in` या `yourdomain.com`) कनेक्ट करें।

### तरीका 2: cPanel / Apache / PHP Shared Hosting पर
अगर आपके पास Hostinger, GoDaddy या cPanel होस्टिंग है:
- फ़ोल्डर की सभी फ़ाइलें `public_html` में अपलोड करें।
- `api/create-order.php` और `verify.php` फ़ाइलें सीधे PHP 7.4/8.x पर चलेंगी।

### तरीका 3: VPS / Cloud Server (Ubuntu / Debian / AWS / Render) पर
- सीधे कमांड चलाएं:
  ```bash
  python3 server.py
  ```
- बैकग्राउंड में चलाने के लिए `pm2` या `systemd` का उपयोग करें:
  ```bash
  pm2 start server.py --name "dhan-book" --interpreter python3
  ```

---

## 🔄 कस्टमर पेमेंट फ्लो (Payment Flow)

```
[ कस्टमर लैंडिंग पेज पर आता है ]
            ↓
[ किसी भी "Get Digital PDF ₹299" बटन पर क्लिक करता है ]
            ↓
[ चेकआउट पॉपअप खुलता है: नाम, ईमेल और मोबाइल नंबर भरता है ]
            ↓
[ "Pay ₹299 & Download" पर क्लिक करता है ]
            ↓
[ सर्वर कैशफ्री प्रोडक्शन API से ऑर्डर बनाता है ]
            ↓
[ कैशफ्री का सुरक्षित पेमेंट गेटवे खुलता है (UPI, GPay, PhonePe, Cards) ]
            ↓
[ कस्टमर ₹299 का भुगतान करता है ]
            ↓
[ कैशफ्री /verify?order_id=... पर रिडायरेक्ट करता है ]
            ↓
[ सर्वर कैशफ्री API से स्टेटस वेरिफाई करता है (PAID) ]
            ↓
[ वेरिफिकेशन सफल होने पर Google Drive का लिंक व डाउनलोड बटन दिखता है ]
            ↓
[ ऑर्डर की जानकारी orders.json में स्वतः दर्ज हो जाती है ]
```
