const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const apiOrderHandler = require('./api/order');

const PORT = process.env.PORT || 8000;

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname || '/';

  // API handler
  if (pathname === '/api/order' || pathname === '/api/create-order') {
    req.query = parsed.query;
    if (req.method === 'POST') {
      let bodyStr = '';
      req.on('data', chunk => { bodyStr += chunk; });
      req.on('end', async () => {
        try { req.body = JSON.parse(bodyStr || '{}'); } catch (e) { req.body = {}; }
        res.status = (code) => { res.statusCode = code; return res; };
        res.json = (data) => {
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify(data));
        };
        await apiOrderHandler(req, res);
      });
      return;
    } else {
      res.status = (code) => { res.statusCode = code; return res; };
      res.json = (data) => {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(data));
      };
      return await apiOrderHandler(req, res);
    }
  }

  // Static images
  if (pathname.startsWith('/images/')) {
    const filePath = path.join(__dirname, pathname);
    if (fs.existsSync(filePath)) {
      const ext = path.extname(filePath).toLowerCase();
      const mime = ext === '.png' ? 'image/png' : 'image/jpeg';
      res.writeHead(200, { 'Content-Type': mime });
      return fs.createReadStream(filePath).pipe(res);
    }
  }

  // Static Policy & Verification Pages
  const staticPages = {
    '/contact': 'contact.html',
    '/contact.html': 'contact.html',
    '/terms': 'terms.html',
    '/terms.html': 'terms.html',
    '/privacy': 'privacy.html',
    '/privacy.html': 'privacy.html',
    '/refund': 'refund.html',
    '/refund.html': 'refund.html',
    '/license': 'license.html',
    '/license.html': 'license.html',
    '/verify': 'verify.html',
    '/verify.html': 'verify.html',
  };

  if (staticPages[pathname]) {
    const p = path.join(__dirname, staticPages[pathname]);
    if (fs.existsSync(p)) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return fs.createReadStream(p).pipe(res);
    }
  }

  // Static Landing Page (Root)
  if (pathname === '/' || pathname === '/index.html') {
    const indexPath = path.join(__dirname, 'index.html');
    if (fs.existsSync(indexPath)) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return fs.createReadStream(indexPath).pipe(res);
    }
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
  });
}

module.exports = server;
