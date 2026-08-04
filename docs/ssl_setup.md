# SSL Setup — Let's Encrypt и production hardening

Nginx уже сконфигурирован на `listen 443 ssl` и работает с self-signed
сертификатами из `docker/certs/` (см. `docker/nginx.conf`). Для продакшена
заменяем self-signed на доверенные сертификаты Let's Encrypt.

## Текущее состояние (dev)

- Self-signed сгенерированы: `docker/certs/fullchain.pem` + `docker/certs/privkey.pem`
  (openssl, 365 дней, CN=localhost).
- Порт 80 остаётся рабочим прокси (health/headers/rate limit) — не редиректит.
- Порт 443 работает с self-signed (проверка: `curl -k https://localhost/health`).

## Переход на Let's Encrypt (production)

1. Настроить DNS A-запись домена на сервер.
2. Поставить certbot на хост (вне контейнера):
   ```bash
   sudo apt-get install -y certbot
   ```
3. Выпустить сертификат (webroot, на работающий порт 80):
   ```bash
   sudo certbot certonly --webroot -w /tmp/acme-challenge -d your-domain.com
   ```
4. Скопировать цепочку в `docker/certs/`:
   ```bash
   sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/certs/fullchain.pem
   sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem  docker/certs/privkey.pem
   sudo chown -R <uid>:<uid> docker/certs/
   ```
5. Перевыпустить nginx-контейнер с новыми сертификатами:
   ```bash
   docker-compose down && docker-compose up -d --build
   ```

## Включение HTTP→HTTPS redirect (301)

Когда сертификат на месте и 443 проверили, включить редирект на 80 порту.
Заменить блок HTTP-`server {}` в `docker/nginx.conf` на редирект:

```nginx
server {
    listen 80;
    server_name _;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    return 301 https://$host$request_uri;
}
```

> **Важно:** после любой правки `nginx.conf` — `nginx -t`.
> Редирект не включаем сразу: он ломает DoD-проверки rate limit (429) и
> headers на localhost:80 (см. Phase 10.3).

## Автообновление (renewal)

Добавить cron для перевыпуска:
```bash
0 3 * * * sudo certbot renew --quiet --deploy-hook \
  "cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /path/to/docker/certs/ && \
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem /path/to/docker/certs/ && \
   docker-compose restart nginx"
```

## Проверки

- `curl -k -I https://localhost` → заголовки X-Frame/X-Content присутствуют.
- `curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health` → 200.
- `docker-compose exec nginx nginx -t` → `syntax is ok`.
