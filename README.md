# ZT-DataEmpresasPriv

## Objetivo

ZT-DataEmpresasPriv es un sistema de prospección comercial de empresas privadas para Zentrix Latam.

Permite:

- Buscar empresas por nichos comerciales.
- Utilizar múltiples proveedores de búsqueda.
- Evitar repetir consultas mediante caché.
- Detectar y deduplicar empresas por dominio.
- Validar webs.
- Crawlear páginas relevantes.
- Usar Playwright cuando una web necesita JavaScript.
- Priorizar páginas de contacto, ventas, comercial, soporte y cotización.
- Guardar HTML localmente.
- Extraer correos y teléfonos públicos.
- Clasificar y priorizar contactos.
- Exportar resultados acumulados a Excel y CSV.

---

## Arquitectura resumida

```text
NICHOS
  ↓
QUERY BUILDER
  ↓
SERPER / TAVILY / EXA
  ↓
SEARCH CACHE
  ↓
DETECCIÓN DE EMPRESAS
  ↓
DEDUP POR DOMINIO
  ↓
VALIDACIÓN WEB
  ↓
SEEDS
  ↓
CRAWLER
requests → Playwright
  ↓
HTML CACHE
  ↓
EMAILS / TELÉFONOS
  ↓
LIMPIEZA
  ↓
EXCEL FINAL
```

---

## Proyecto incremental

La información persistente se guarda principalmente en:

```text
data/cache/
```

Archivos importantes:

```text
search_queries.csv
search_results.csv
company_candidates.csv
companies_master.csv
web_validated.csv
crawl_seeds.csv
crawled_pages.csv
crawl_seed_log.csv
contact_extract_page_log.csv
emails_found.csv
emails_found_clean.csv
emails_rejected.csv
emails_by_company_clean.csv
phones_found.csv
html/
```

No borrar `data/cache/` salvo que se desee reiniciar el proyecto.

---

## Proveedores de búsqueda

Configurados en:

```text
config/search_providers.yaml
```

Prioridad actual:

```text
1. Serper
2. Tavily
3. Exa
```

Variables:

```env
SERPER_API_KEY=
TAVILY_API_KEY=
EXA_API_KEY=
```

Las claves reales deben estar únicamente en `.env`.

---

## Instalación

Crear entorno:

```bash
python3 -m venv .venv
```

Activar en macOS:

```bash
source .venv/bin/activate
```

Instalar:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

---

## Comandos principales

```bash
python main.py build-queries --niche leasing_laptops

python main.py search   --niche leasing_laptops   --limit-queries 2

python main.py companies

python main.py validate-webs

python main.py crawl-seeds

python main.py crawl   --limit-companies 2   --max-pages 8

python main.py extract-emails

python main.py clean-emails

python main.py export-final
```

---

## Salidas

```text
data/output/ZT_DataEmpresasPriv.xlsx
data/output/ZT_DataEmpresasPriv_YYYY-MM-DD.xlsx
data/output/ZT_DataEmpresasPriv.csv
```

---

## Documentación complementaria

```text
MANUAL_USUARIO.md
ARQUITECTURA_DESARROLLO.md
FLUJO_SISTEMA.md
MANTENIMIENTO.md
EJECUCION_DIARIA_3_PROYECTOS.md
```
