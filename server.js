const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const apiOrderHandler = require('./api/order');

// Pre-load all HTML files statically so Vercel Node File Trace (NFT) bundles them
const indexHtml = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8');
const contactHtml = fs.readFileSync(path.join(__dirname, 'contact.html'), 'utf-8');
const termsHtml = fs.readFileSync(path.join(__dirname, 'terms.html'), 'utf-8');
const privacyHtml = fs.readFileSync(path.join(__dirname, 'privacy.html'), 'utf-8');
const refundHtml = fs.readFileSync(path.join(__dirname, 'refund.html'), 'utf-8');
const licenseHtml = fs.readFileSync(path.join(__dirname, 'license.html'), 'utf-8');
const verifyHtml = fs.readFileSync(path.join(__dirname, 'verify.html'), 'utf-8');

const htmlPages = {
  '/': indexHtml,
  '/index.html': indexHtml,
  '/contact': contactHtml,
  '/contact.html': contactHtml,
  '/terms': termsHtml,
  '/terms.html': termsHtml,
  '/privacy': privacyHtml,
  '/privacy.html': privacyHtml,
  '/refund': refundHtml,
  '/refund.html': refundHtml,
  '/license': licenseHtml,
  '/license.html': licenseHtml,
  '/verify': verifyHtml,
  '/verify.html': verifyHtml
};

const handler = async (req, res) => {
  const parsed = url.parse(req.url, true);
  let pathname = parsed.pathname || '/';
  if (pathname.length > 1 && pathname.endsWith('/')) {
    pathname = pathname.slice(0, -1);
  }

  // Response helpers for Express/Vercel compatibility
  if (!res.status) {
    res.status = (code) => { res.statusCode = code; return res; };
  }
  if (!res.json) {
    res.json = (data) => {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(data));
    };
  }

  // 1. API: /api/order & /api/create-order
  if (pathname === '/api/order' || pathname === '/api/create-order') {
    req.query = parsed.query;
    if (req.method === 'POST') {
      let bodyStr = '';
      if (req.body) {
        bodyStr = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
      } else {
        bodyStr = await new Promise(resolve => {
          let b = '';
          req.on('data', chunk => b += chunk);
          req.on('end', () => resolve(b));
        });
      }
      try { req.body = JSON.parse(bodyStr || '{}'); } catch (e) { req.body = {}; }
      return await apiOrderHandler(req, res);
    } else {
      return await apiOrderHandler(req, res);
    }
  }

  // 2. Preloaded HTML Pages (Instant in-memory delivery)
  if (htmlPages[pathname]) {
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'public, max-age=0, must-revalidate'
    });
    return res.end(htmlPages[pathname]);
  }

  // 3. Static Images
  if (pathname.startsWith('/images/')) {
    const filePath = path.join(__dirname, pathname);
    if (fs.existsSync(filePath)) {
      const ext = path.extname(filePath).toLowerCase();
      const mime = ext === '.png' ? 'image/png' : 'image/jpeg';
      res.writeHead(200, {
        'Content-Type': mime,
        'Cache-Control': 'public, max-age=31536000, immutable'
      });
      return fs.createReadStream(filePath).pipe(res);
    }
  }

  // 4. Default fallback: serve Landing Page
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  return res.end(indexHtml);
};

// Export handler for Vercel Serverless Function
module.exports = handler;

// Local Node.js server support
if (!process.env.VERCEL) {
  const PORT = process.env.PORT || 3000;
  const server = http.createServer(handler);
  server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
  });
}
