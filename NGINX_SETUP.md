# Nginx Reverse Proxy & DuckDNS SSL Setup

### 1. Install Dependencies
```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-dns-duckdns
```

### 2. Nginx Proxy Configuration
 Use your domain. Do not include http://.

Create `/etc/nginx/sites-available/<your_domain>`:
```nginx
server {
    listen 80;
    server_name <your_domain>; 

    location / {
        proxy_pass http://[IP_ADDRESS]:2586;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```
**Enable & Restart:**
```bash
sudo ln -s /etc/nginx/sites-available/<your_domain> /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```
Sample SSL conf for DuckDNS provider, you can choose other providers as well.
### 3. DuckDNS DNS Challenge
```bash
# Set credentials
mkdir -p ~/.secrets/certbot
echo "dns_duckdns_token = YOUR_TOKEN" > ~/.secrets/certbot/duckdns.ini
chmod 600 ~/.secrets/certbot/duckdns.ini

# Get Certificate (Use domain only, no http)
sudo certbot certonly \
  --authenticator dns-duckdns \
  --dns-duckdns-credentials ~/.secrets/certbot/duckdns.ini \
  -d <your_domain>
```

### 4. Enable SSL in Nginx
Update `/etc/nginx/sites-available/<your_domain>`:
```nginx
server {
    listen 443 ssl;
    server_name <your_domain>;

    ssl_certificate /etc/letsencrypt/live/<your_domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<your_domain>/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:2586;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
    }
}
```
**Final Reload:**
```bash
sudo nginx -t && sudo systemctl reload nginx
```
