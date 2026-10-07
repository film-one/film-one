# film.one Catalog API

Սա optional server-side API-ն է։ Հիմնական catalog browse/search-ը կարող է աշխատել GitHub Pages static catalog-ով, իսկ այս API-ն անհրաժեշտ է, եթե ուզում ես server-side TMDB search և TV-ի մանրամասն seasons/episodes տվյալներ։

## Environment

```bash
export TMDB_API_KEY="YOUR_TMDB_KEY"
export FILM_ONE_ADMIN_TOKEN="YOUR_LONG_RANDOM_TOKEN"
python3 server.py
```

Endpoints:

- `GET /api/search?q=...` — public TMDB metadata search, առանց TMDB key-ը Android-ում պահելու
- `GET /api/title?type=tv&id=...` — TV details + seasons/credits
- `GET /api/admin/search?q=...&token=...` — admin search
- `POST /api/add?token=...` — legacy manual catalog add

Production-ում օգտագործիր HTTPS reverse proxy (Nginx/Caddy) և պահիր secrets-ը միայն server environment-ում։

Android-ում `app/src/main/assets/config.json`-ի `api_base_url`-ը կարող է մնալ դատարկ․ այդ դեպքում որոնումը օգտագործում է GitHub Pages-ի static search shards-ը։ Եթե API-ն deploy անես, այստեղ դիր նրա HTTPS URL-ը՝ server-side TMDB search և series details ստանալու համար։
