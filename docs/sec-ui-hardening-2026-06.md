# Säkerhetshärdning av UI:t — juni 2026

**Datum:** 2026-06-11
**Branch/PR:** `sec/ui-hardening` (stacked på `fix/ui-polish`, PR #79)
**Omfattning:** `app/static/` (UI), `app/main.py` (headers-middleware),
`docker/nginx/default.conf`, `tests/`

Det här dokumentet beskriver fyra härdningsåtgärder som gjordes efter en
egen säkerhetsgenomgång av den statiska UI:n, samt motiveringen bakom
varje val. Genomgången gjordes i post-delivery-läge med OWASP Top 10
som referens.

---

## 1. Stored XSS via threat intel-feeds (åtgärdad)

### Risken

UI:t renderade data från externa threat intel-källor som rå HTML på två
ställen:

- **Kartans popups** (`renderThreatMap`): `item.ioc`, `malware_family`,
  `city` m.fl. interpolerades i en HTML-sträng som gavs till Leaflets
  `bindPopup()`, som tolkar strängar som HTML.
- **KEV-panelen** (`renderThreatFeed`): `vendor`/`product` från CISA
  KEV-feeden sattes via `innerHTML`.

Det allvarliga fallet är URLhaus: feedens *innehåll* är URL:er inskickade
av tredje part — alltså per definition angriparpåverkad data. En IOC-URL
som innehåller t.ex. `<img src=x onerror=...>` hade exekverat skript i
besökarens webbläsare när popupen öppnades. Detta är en klassisk **stored
XSS** där lagringsplatsen är vår egen Mongo (`threat_events`) och källan
är extern. Backend (`app/services/threat_intel.py`) sanerar medvetet inte
fälten — data ska lagras rått och **escapas vid presentation**, vilket är
rätt princip; felet var att presentationen inte gjorde det.

### Åtgärden

All rendering av extern data bygger nu DOM-noder med `textContent`:

- Popups byggs i nya `threatPopupContent()` som returnerar ett
  DOM-element (text-noder + `<br>`), aldrig en HTML-sträng.
- KEV-raderna återanvänder befintliga `detailRow()` (som redan var
  korrekt skriven med `textContent`).
- Felmeddelande-raden i `loadUploads` bytte också från `innerHTML` till
  `textContent` för konsekvens, trots att strängarna där är lokala
  konstanter.

**Princip att ta med till rapporten:** kontextuell output-encoding vid
presentationsskiktet, inte sanering vid lagring. Webbläsaren gör
escapningen åt oss gratis via `textContent`.

## 2. Säkerhetsheaders flyttade till applikationen + CSP (ny)

### Risken

Säkerhetsheaders (`X-Content-Type-Options`, `X-Frame-Options`, m.fl.)
sattes bara i Compose-nginxen (`docker/nginx/default.conf`). Men i
produktion är request-vägen **k3s ingress-nginx → uvicorn** och på
Render finns ingen proxy alls — i båda fallen levererades sidan **utan
en enda säkerhetsheader**. Klassiskt miljöparitetsproblem: skyddet fanns
bara i miljön där det behövdes minst.

### Åtgärden

- **Middleware i FastAPI** (`app/main.py`) sätter nu headers på alla
  svar. Appen är den enda komponent som finns i *alla* miljöer, därför
  är den rätt plats — "single source of truth".
- Headers i nginx-configen **togs bort** (kommentar förklarar varför):
  dubbletter kan ge två `X-Frame-Options`-headers, vilket webbläsare
  kan tolka oförutsägbart eller förkasta.
- **`X-XSS-Protection` togs bort helt.** Headern är deprecated; dess
  XSS-auditor är borttagen ur moderna webbläsare och kunde i äldre
  webbläsare introducera egna sårbarheter (XS-leaks). Modern
  rekommendation (MDN/OWASP) är att inte sätta den — CSP ersätter den.
- **Content-Security-Policy är ny** och är defense-in-depth mot bl.a.
  XSS-klassen i punkt 1:

  ```
  default-src 'self';
  script-src 'self' https://unpkg.com;
  style-src 'self' https://unpkg.com https://fonts.googleapis.com;
  font-src https://fonts.gstatic.com;
  img-src 'self' data: https://unpkg.com https://*.basemaps.cartocdn.com;
  connect-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none'
  ```

  Varje källa motsvarar ett faktiskt behov: Leaflet/markercluster
  (unpkg), Google Fonts, CARTO-kartrutor. `connect-src 'self'` innebär
  att skript bara kan ringa vårt eget API — exfiltration till externa
  hosts blockeras även om ett skript skulle injiceras.

### Två medvetna avvägningar

1. **Ingen `'unsafe-inline'`.** Det krävde att UI:ts inline-`<script>`
   (~590 rader) flyttades till `app/static/app.js`. Utan flytten hade
   CSP:n behövt tillåta inline-skript, vilket hade gjort den nästan
   verkningslös mot XSS.
2. **`/docs` och `/redoc` är undantagna från CSP** (övriga headers
   gäller fortfarande). FastAPI:s Swagger UI laddar sina assets från
   en extern CDN som UI-policyn inte ska behöva tillåta. Undantaget är
   exakt och dokumenterat i koden.

## 3. Subresource Integrity på CDN-beroenden (supply chain)

### Risken

`leaflet.js` laddades redan med `integrity`-hash, men
`leaflet.markercluster.js` och dess två CSS-filer från unpkg saknade
SRI. Om unpkg eller paketet komprometteras (jfr `event-stream`,
`polyfill.io`) hade skadlig kod körts direkt på vår sida — på en sajt
vars syfte är att demonstrera säkerhet.

### Åtgärden

SRI-hashar (`sha384`) + `crossorigin` på alla tre resurserna.
Hasharna räknades fram från exakt de bytes unpkg serverar, och metoden
verifierades genom att räkna om leaflets befintliga, kända hash
(matchade). Webbläsaren vägrar nu exekvera/applicera filerna om
innehållet ändras en enda byte. Pinnad version (`@1.5.3`) + SRI ger
samma garanti som image-digests i K8s-manifesten — samma princip,
annat lager.

## 4. Småfixar

- **`upload-details`-synlighet styrdes av tre mekanismer** (`hidden`,
  `style.display`, CSS-klassen `is-open`). Nu styr enbart `is-open` +
  befintliga CSS-regler. Färre tillstånd som kan glida isär.
- **Språkkonsekvens:** tre svenska värdesträngar i ML/threat
  intel-raderna byttes till engelska (`MATCH - known malicious hash`,
  `No match`, `No ML data`). Beslut: UI:t är och förblir konsekvent
  engelskt (`lang="en"`, så levererades och presenterades produkten);
  projektdokumentation och commits förblir svenska. CLAUDE.md (lokal)
  är uppdaterad med beslutet.

## Verifiering

- `ruff check app tests` — grönt.
- Nya tester i `tests/test_security_headers.py`: headers på `/health`,
  CSP på `/` och `/static/*`, CSP-undantaget på `/docs`, samt att
  `X-XSS-Protection` inte återinförs.
- Manuell verifiering lokalt: sidan laddad med DevTools-konsolen öppen —
  inga CSP-violations; karta, kluster, fonts och tiles renderar.
- Efter deploy: kontrollera prod-headers med
  `curl -sI https://sentinel-upload.secion.se | grep -iE 'content-security|x-frame|x-content'`
  och gärna https://securityheaders.com.

## Kvar att överväga (medvetet utanför denna PR)

- `Strict-Transport-Security` (HSTS) — bör sättas, men kräver beslut om
  `max-age`/`includeSubDomains` eftersom `secion.se` har fler subdomäner.
- Self-hosta Leaflet/fonts och strama åt CSP:n ytterligare (tar bort
  unpkg/Google som tillåtna källor helt).
- CSP `report-to`/`report-uri` för att få telemetri på violations.
