# Manual de Usuario — ZT-DataEmpresasPriv

## 1. Activar proyecto

### macOS

```bash
cd /Users/USUARIO/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv
source .venv/bin/activate
```

Verificar:

```bash
pwd
which python
```

### Windows PowerShell

```powershell
cd C:\datoszentrixlatam\ZT-DataEmpresasPriv
.\.venv\Scripts\Activate.ps1
```

---

## 2. Primera instalación

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

---

## 3. Configurar APIs

Archivo:

```text
.env
```

Contenido:

```env
SERPER_API_KEY=
TAVILY_API_KEY=
EXA_API_KEY=
```

Nunca subir `.env` a Git ni compartirlo dentro de documentación.

---

## 4. Crear queries

```bash
python main.py build-queries   --niche leasing_laptops
```

Genera:

```text
data/cache/search_queries.csv
data/processed/YYYY-MM-DD/search_queries.csv
```

---

## 5. Ejecutar búsquedas

Prueba pequeña:

```bash
python main.py search   --niche leasing_laptops   --limit-queries 2
```

El límite se aplica sobre queries pendientes.

Por ejemplo:

```text
Queries totales : 10
Queries cacheadas : 2
Queries a ejecutar : 2
```

Las dos primeras no se repiten.

---

## 6. Detectar empresas

```bash
python main.py companies
```

Genera:

```text
data/cache/company_candidates.csv
data/cache/companies_master.csv
```

La deduplicación se realiza por dominio raíz.

---

## 7. Validar webs

```bash
python main.py validate-webs
```

Genera:

```text
data/cache/web_validated.csv
```

Las webs ya validadas correctamente quedan en caché.

---

## 8. Generar seeds

```bash
python main.py crawl-seeds
```

Genera:

```text
data/cache/crawl_seeds.csv
```

---

## 9. Crawlear pocas empresas

Ejemplo:

```bash
python main.py crawl   --limit-companies 2   --max-pages 8
```

El crawler prioriza:

```text
contacto
contactanos
ventas
comercial
cotizar
asesor
soporte
servicio técnico
WhatsApp
nosotros
empresa
```

---

## 10. Requests y Playwright

Primero usa:

```text
requests
```

Si la página requiere JavaScript o tiene muy poco contenido visible, utiliza:

```text
Playwright + Chromium
```

Esto permite trabajar con sitios React, Vite, Vue, Angular, Next.js y similares.

Los HTML se guardan en:

```text
data/cache/html/<COMPANY_KEY>/<PAGE_KEY>.html
```

---

## 11. Extraer contactos

```bash
python main.py extract-emails
```

Genera:

```text
data/cache/emails_found.csv
data/cache/phones_found.csv
data/cache/contact_extract_page_log.csv
```

Esta etapa trabaja sobre los HTML guardados y no vuelve a visitar las webs.

---

## 12. Limpiar contactos

```bash
python main.py clean-emails
```

Genera:

```text
data/cache/emails_found_clean.csv
data/cache/emails_rejected.csv
data/cache/emails_by_company_clean.csv
```

Clasificaciones principales:

```text
DOMINIO_OFICIAL
PUBLICO_GENERICO
DOMINIO_EXTERNO_PUBLICADO
```

Áreas:

```text
VENTAS
COMERCIAL
CONTACTO
SOPORTE
LOGISTICA
ADMINISTRACION
GERENCIA
MARKETING
RRHH
GENERAL
```

---

## 13. Exportar Excel

```bash
python main.py export-final
```

Salidas:

```text
data/output/ZT_DataEmpresasPriv.xlsx
data/output/ZT_DataEmpresasPriv_YYYY-MM-DD.xlsx
data/output/ZT_DataEmpresasPriv.csv
```

---

## 14. Flujo normal completo

```bash
python main.py build-queries --niche leasing_laptops
python main.py search --niche leasing_laptops
python main.py companies
python main.py validate-webs
python main.py crawl-seeds
python main.py crawl --max-pages 8
python main.py extract-emails
python main.py clean-emails
python main.py export-final
```

---

## 15. Prueba pequeña

```bash
python main.py search   --niche leasing_laptops   --limit-queries 2
```

Luego:

```bash
python main.py companies
python main.py validate-webs
python main.py crawl-seeds
python main.py crawl --limit-companies 1 --max-pages 8
python main.py extract-emails
python main.py clean-emails
python main.py export-final
```

---

## 16. Qué no borrar

No borrar normalmente:

```text
data/cache/
```

Especialmente:

```text
search_results.csv
companies_master.csv
web_validated.csv
crawled_pages.csv
crawl_seed_log.csv
contact_extract_page_log.csv
html/
```
