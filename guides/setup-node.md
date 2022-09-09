```
   ▄█   ▄█▄ ███    █▄     ▄████████    ▄████████   ▄▄▄▄███▄▄▄▄      ▄████████ 
  ███ ▄███▀ ███    ███   ███    ███   ███    ███ ▄██▀▀▀███▀▀▀██▄   ███    ███ 
  ███▐██▀   ███    ███   ███    █▀    ███    ███ ███   ███   ███   ███    ███ 
 ▄█████▀    ███    ███   ███          ███    ███ ███   ███   ███   ███    ███ 
▀▀█████▄    ███    ███ ▀███████████ ▀███████████ ███   ███   ███ ▀███████████ 
  ███▐██▄   ███    ███          ███   ███    ███ ███   ███   ███   ███    ███ 
  ███ ▀███▄ ███    ███    ▄█    ███   ███    ███ ███   ███   ███   ███    ███ 
  ███   ▀█▀ ████████▀   ▄████████▀    ███    █▀   ▀█   ███   █▀    ███    █▀  
  ▀                                 ExPeCt ChAoS                                              
```
---
Node setup
=

**server specification**: `8GB RAM / 4 Cores / 160GB Storage`

### pre-requisites
```shell
sudo apt-get install nginx
curl https://getsubstrate.io -sSf | bash   
```
```diff
- Exit SSH session for installed libs to take affect.
```

### clone & build
```shell
git clone https://github.com/paritytech/polkadot kusama
mkdir kusama && cd kusama
./scripts/init.sh
cargo build --release
```

### Start the syncing process with Kusama's mainnet
This can take 1 - 2 days to fully sync unless you specify `--sync fast`  
Run `./target/release/polkadot --help` for more information
```shell
./target/release/polkadot --name "<NODE-NAME>" --chain kusama --blocks-pruning 103000 --state-pruning 103000 --rpc-cors all
```
---

Set up a self-signed certificate
=
```shell
sudo openssl req -x509 -nodes -days 1095 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt
```
---

Set up Nginx server
=
Now it's time to tell Nginx to use these certificates.  
The server block below is all you need, but keep in mind that you need to replace some placeholder values. Notably:
```
SERVER_ADDRESS should be replaced by your domain name if you have it, 
        or your server's IP address if not.
        
CERT_LOCATION should be /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem if you used Certbot, 
        or /etc/ssl/certs/nginx-selfsigned.crt if self-signed.
        
CERT_LOCATION_KEY should be /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem if you used Certbot, 
        or /etc/ssl/private/nginx-selfsigned.key if self-signed.
        
CERT_DHPARAM should be /etc/letsencrypt/ssl-dhparams.pem if you used Certbot, 
        and /etc/ssl/certs/dhparam.pem if self-signed.
```

Create nginx config:
```shell
nano /etc/nginx/sites-available/kusama
```

```
server {

        server_name SERVER_ADDRESS;

        root /var/www/html;
        index index.html;

        location / {
          try_files $uri $uri/ =404;

          proxy_buffering off;
          proxy_pass http://localhost:9944;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header Host $host;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
        }

        listen [::]:443 ssl ipv6only=on;
        listen 443 ssl;
        ssl_certificate CERT_LOCATION;
        ssl_certificate_key CERT_LOCATION_KEY;

        ssl_session_cache shared:cache_nginx_SSL:1m;
        ssl_session_timeout 1440m;

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_prefer_server_ciphers on;

        ssl_ciphers "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS";

        ssl_dhparam CERT_DHPARAM;
        
}
```
ctrl + x to save

#### enable nginx config
```shell
ln -s /etc/nginx/sites-available/kusama /etc/nginx/sites-enabled/
systemctl restart nginx.service
systemctl status nginx.service
```
Run the following command to see errors in detail if `systemctl status`  is not successful
```shell
journalctl -xe
```
---
Daemonize with systemd
=
```shell
nano /etc/systemd/system/kusama-node.service
```

```
[Unit]
Description=Kusama Node

[Service]
ExecStart=/root/kusama/./target/release/polkadot --name "<NODE-NAME>" --chain kusama --blocks-pruning 103000 --state-pruning 103000 --rpc-cors all
Restart=always
RestartSec=120

[Install]
WantedBy=multi-user.target
```
ctrl + x to save
```shell
systemctl enable /etc/systemd/system/kusama-node.service
systemctl status kusama-node.service
```
---
Search for your node on [telemetry](https://telemetry.polkadot.io/#list/0xb0a8d493285c2df73290dfb7e61f870f17b41801197a149ca93654499ea3dafe)