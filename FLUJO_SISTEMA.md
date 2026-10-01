# Flujo del Sistema — ZT-DataEmpresasPriv

## Flujo completo

```text
INICIO
  ↓
NICHOS
  ↓
BUILD QUERIES
  ↓
¿QUERY EN CACHE?
  ├── SÍ → OMITIR
  └── NO
       ↓
     SERPER
       ↓
   ¿RESULTADO?
       ├── SÍ → GUARDAR
       └── NO/ERROR
              ↓
            TAVILY
              ↓
            EXA
       ↓
SEARCH RESULTS
       ↓
DETECTAR DOMINIO
       ↓
DEDUP EMPRESA
       ↓
COMPANY_KEY
       ↓
VALIDAR WEB
       ↓
¿WEB OK?
  ├── NO → REGISTRAR
  └── SÍ
       ↓
GENERAR SEEDS
       ↓
¿SEED PROCESADA?
  ├── SÍ → OMITIR
  └── NO
       ↓
REQUESTS
       ↓
¿NECESITA JS?
  ├── NO → HTML
  └── SÍ → PLAYWRIGHT → HTML
       ↓
BUSCAR CONTACTO
       ↓
CONTACTO / VENTAS / COMERCIAL / SOPORTE
       ↓
GUARDAR HTML
       ↓
EXTRAER EMAILS / TELÉFONOS
       ↓
LIMPIAR / CLASIFICAR
       ↓
EXPORTAR EXCEL
       ↓
FIN
```

---

## Flujo incremental

```text
QUERY_KEY
  ↓
COMPANY_KEY
  ↓
VALIDATION_KEY
  ↓
SEED_KEY
  ↓
PAGE_KEY
  ↓
EMAIL_KEY / PHONE_KEY
```

Cada etapa usa una clave estable.

---

## Flujo de contacto

```text
HOME
  ↓
EXTRAER LINKS
  ↓
PRIORIDAD 1
  ├── contacto
  ├── ventas
  ├── comercial
  ├── cotizar
  ├── asesor
  ├── soporte
  └── whatsapp
  ↓
PRIORIDAD 2
  ├── nosotros
  ├── empresa
  ├── servicios
  ├── leasing
  └── alquiler
```

---

## Flujo Playwright

```text
REQUESTS
  ↓
texto visible
  ↓
¿muy poco contenido / SPA?
  ├── NO → usar HTML requests
  └── SÍ
       ↓
   Playwright
       ↓
   Chromium
       ↓
   HTML renderizado
```

---

## Comandos del flujo

```bash
python main.py build-queries --niche leasing_laptops
python main.py search --niche leasing_laptops --limit-queries 2
python main.py companies
python main.py validate-webs
python main.py crawl-seeds
python main.py crawl --limit-companies 2 --max-pages 8
python main.py extract-emails
python main.py clean-emails
python main.py export-final
```
