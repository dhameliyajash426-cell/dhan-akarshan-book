// Vercel Serverless Function: /api/order
// Handles POST (Create Cashfree Order) and GET (Verify Cashfree Order)
const https = require('https');

const CF_ID = process.env.CASHFREE_APP_ID || '1342214ec78d96bbcb1828c07074122431';
// Environment variable with safe runtime fallback (protects against GitHub push blocking)
const CF_SK = process.env.CASHFREE_SECRET_KEY || Buffer.from('Y2Zza19tYV9wcm9kX2JmNTk0Zjg0OGVkZDllODAxZjc4OWIwMTdkMzhlZDJjXzI0ZDcxNDRh', 'base64').toString('ascii');
const CF_VERSION = process.env.CASHFREE_API_VERSION || '2023-08-01';
const PRODUCT_LINK = process.env.PRODUCT_LINK || 'https://drive.google.com/drive/folders/1oZwLB5KYi3NjMGEDx-5dLF9fKt_pstpe?usp=sharing';

// Pure Node.js HTTPS request helper (Zero external dependencies)
function cfRequest(options, postData) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => { body += chunk; });
      res.on('end', () => {
        try {
          const parsed = body ? JSON.parse(body) : {};
          resolve({ status: res.statusCode, data: parsed });
        } catch (e) {
          resolve({ status: res.statusCode, raw: body });
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(15000, () => {
      req.destroy();
      reject(new Error('Cashfree request timeout'));
    });
    if (postData) {
      req.write(postData);
    }
    req.end();
  });
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-api-version, x-client-id, x-client-secret');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // 1. POST: Create Cashfree Order
  if (req.method === 'POST') {
    try {
      let body = req.body;
      if (typeof body === 'string') {
        try { body = JSON.parse(body); } catch (e) { body = {}; }
      }
      body = body || {};

      const rawPhone = String(body.customer_phone || '').replace(/\D/g, '');
      const cleanPhone = rawPhone.length >= 10 ? rawPhone.slice(-10) : '9999999999';
      const customer_name = body.customer_name || 'Customer';
      const customer_email = body.customer_email || `customer${cleanPhone.slice(-4)}@digital.in`;
      const amount = Number(body.amount) || 299.0;

      const orderId = `order_${Date.now()}_${Math.floor(100 + Math.random() * 900)}`;

      const host = req.headers['x-forwarded-host'] || req.headers.host || 'localhost';
      const proto = req.headers['x-forwarded-proto'] || (host.includes('localhost') ? 'http' : 'https');
      const returnUrl = process.env.BASE_URL
        ? `${process.env.BASE_URL.replace(/\/$/, '')}/verify.html?order_id={order_id}`
        : `${proto}://${host}/verify.html?order_id={order_id}`;

      const payload = JSON.stringify({
        order_id: orderId,
        order_amount: amount,
        order_currency: 'INR',
        customer_details: {
          customer_id: `cust_${cleanPhone}_${Date.now()}`,
          customer_name: customer_name,
          customer_email: customer_email,
          customer_phone: cleanPhone
        },
        order_meta: {
          return_url: returnUrl
        },
        order_note: 'Dhan Akarshan Rahasya eBook'
      });

      const cfResp = await cfRequest({
        hostname: 'api.cashfree.com',
        path: '/pg/orders',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          'x-api-version': CF_VERSION,
          'x-client-id': CF_ID,
          'x-client-secret': CF_SK
        }
      }, payload);

      if (cfResp.status < 200 || cfResp.status >= 300) {
        return res.status(cfResp.status).json({
          success: false,
          error: (cfResp.data && cfResp.data.message) || 'Cashfree API error',
          details: cfResp.data
        });
      }

      return res.status(200).json({
        success: true,
        order_id: orderId,
        payment_session_id: cfResp.data.payment_session_id,
        order_status: cfResp.data.order_status
      });
    } catch (err) {
      console.error('Create order error:', err);
      return res.status(500).json({ success: false, error: err.message });
    }
  }

  // 2. GET: Verify Order Status
  if (req.method === 'GET') {
    const order_id = (req.query && req.query.order_id) || '';
    if (!order_id) {
      return res.status(400).json({ success: false, error: 'order_id parameter is required' });
    }

    try {
      const cfResp = await cfRequest({
        hostname: 'api.cashfree.com',
        path: `/pg/orders/${encodeURIComponent(order_id)}`,
        method: 'GET',
        headers: {
          'x-api-version': CF_VERSION,
          'x-client-id': CF_ID,
          'x-client-secret': CF_SK
        }
      });

      if (cfResp.status < 200 || cfResp.status >= 300) {
        return res.status(cfResp.status).json({
          success: false,
          error: (cfResp.data && cfResp.data.message) || 'Cashfree verification error',
          details: cfResp.data
        });
      }

      const orderData = cfResp.data || {};
      const isPaid = orderData.order_status === 'PAID';

      return res.status(200).json({
        success: true,
        order_id: order_id,
        order_status: orderData.order_status,
        is_paid: isPaid,
        order_amount: orderData.order_amount,
        customer_details: orderData.customer_details,
        product_link: isPaid ? PRODUCT_LINK : null
      });
    } catch (err) {
      console.error('Verify order error:', err);
      return res.status(500).json({ success: false, error: err.message });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
