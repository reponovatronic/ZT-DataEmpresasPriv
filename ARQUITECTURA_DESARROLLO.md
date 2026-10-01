# Arquitectura de Desarrollo — ZT-DataEmpresasPriv

## 1. Principio principal

El sistema está diseñado para ser incremental.

La regla es:

> Si una query, empresa, web, seed, página o contacto ya fue procesado correctamente, no debe volver a generar consumo innecesario.

---

## 2. Arquitectura

```text
config/niches.yaml
        ↓
QueryBuilder
        ↓
SearchManager
        ↓
Serper → Tavily → Exa
        ↓
search_results.csv
        ↓
CompanyCandidateScorer
        ↓
companies_master.csv
        ↓
WebValidator
        ↓
web_validated.csv
        ↓
CrawlSeedBuilder
        ↓
crawl_seeds.csv
        ↓
SiteCrawler
        ↓
requests / Playwright
        ↓
HTML cache
        ↓
EmailExtractor
        ↓
EmailCleaner
        ↓
FinalExporter
```

---

## 3. Query Builder

Archivo:

```text
src/search/query_builder.py
```

Clave:

```text
BASE_QUERY_KEY = SHA1(niche_id + query)
```

Salida:

```text
data/cache/search_queries.csv
```

---

## 4. Search Manager

Archivo:

```text
src/search/search_manager.py
```

Prioridad:

```text
Serper
  ↓
Tavily
  ↓
Exa
```

Estados:

```text
OK
NO_RESULTS
NO_RESULTS_FINAL
ERROR
```

Una query queda finalizada cuando existe:

```text
OK
```

o:

```text
NO_RESULTS_FINAL
```

---

## 5. Company Discovery

Archivo:

```text
src/validate/company_candidate_scorer.py
```

Clave:

```text
COMPANY_KEY = SHA1(ROOT_DOMAIN)
```

Ejemplo:

```text
www.empresa.com
empresa.com/contacto
empresa.com/servicios
```

se consolidan como:

```text
empresa.com
```

---

## 6. Web Validator

Archivo:

```text
src/validate/web_validator.py
```

Clave:

```text
VALIDATION_KEY = SHA1(COMPANY_KEY + URL)
```

Salida:

```text
data/cache/web_validated.csv
```

---

## 7. Crawl Seed Builder

Archivo:

```text
src/crawler/crawl_seed_builder.py
```

Tipos de seed:

```text
WEB_VALIDATED
HOME
SEARCH_RESULT
```

Salida:

```text
data/cache/crawl_seeds.csv
```

---

## 8. Site Crawler

Archivo:

```text
src/crawler/site_crawler.py
```

Clave:

```text
PAGE_KEY = SHA1(COMPANY_KEY + PAGE_URL)
```

Prioridad alta:

```text
contacto
contact
contactanos
ventas
comercial
cotizar
asesor
soporte
whatsapp
```

Prioridad media:

```text
nosotros
empresa
quienes somos
leasing
renting
alquiler
servicios
```

Rutas fallback:

```text
/contacto
/contact
/contactanos
/contact-us
/ventas
/comercial
/cotiza
/cotizar
/soporte
/servicio-tecnico
/nosotros
/quienes-somos
/empresa
```

---

## 9. Requests y Playwright

```text
requests
   ↓
¿HTML suficiente?
   ├── Sí → guardar
   └── No / SPA
          ↓
      Playwright
          ↓
      Chromium
          ↓
       guardar HTML
```

---

## 10. HTML cache

Ruta:

```text
data/cache/html/<COMPANY_KEY>/<PAGE_KEY>.html
```

Este cache debe conservarse en migraciones.

---

## 11. Contact Extractor

Archivo:

```text
src/extract/email_extractor.py
```

Entradas:

```text
crawled_pages.csv
HTML cache
```

Salidas:

```text
emails_found.csv
phones_found.csv
contact_extract_page_log.csv
```

---

## 12. Email Cleaner

Archivo:

```text
src/extract/email_cleaner.py
```

Clasifica:

```text
DOMINIO_OFICIAL
PUBLICO_GENERICO
DOMINIO_EXTERNO_PUBLICADO
```

y prioriza áreas comerciales.

---

## 13. Final Exporter

Archivo:

```text
src/export/final_exporter.py
```

Salidas:

```text
ZT_DataEmpresasPriv.xlsx
ZT_DataEmpresasPriv_YYYY-MM-DD.xlsx
ZT_DataEmpresasPriv.csv
```

---

## 14. Estado persistente

Debe mantenerse:

```text
data/cache/
```

Incluye:

```text
queries
resultados
empresas
webs
seeds
páginas
HTML
emails
teléfonos
logs internos
```

---

## 15. Escalabilidad

La arquitectura permite añadir:

- Más nichos.
- Más proveedores.
- Más heurísticas de contacto.
- Extracción de WhatsApp.
- Formularios.
- LinkedIn corporativo.
- Clasificación con IA.
- Scoring comercial.
- Integración con CRM.
