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

## Instalación del entorno virtual

Antes de ejecutar el proyecto, se debe crear un entorno virtual e instalar las dependencias.

### Instalación en macOS

Entrar al proyecto:

```bash
cd /Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv
```

Crear entorno virtual:

```bash
python3 -m venv .venv
```

Activar entorno virtual:

```bash
source .venv/bin/activate
```

Actualizar `pip`:

```bash
python -m pip install --upgrade pip
```

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

Instalar Chromium para Playwright:

```bash
python -m playwright install chromium
```

Verificar instalación:

```bash
python --version
which python
python -m pip -V
```

El `which python` debe apuntar a una ruta similar a:

```text
/Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv/.venv/bin/python
```

---

### 1 Instalación en Windows

Entrar al proyecto:

```powershell
cd C:\datoszentrixlatam\ZT-DataEmpresasPriv
```

Crear entorno virtual:

```powershell
python -m venv .venv
```

Activar entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Actualizar `pip`:

```powershell
python -m pip install --upgrade pip
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Instalar Chromium para Playwright:

```powershell
python -m playwright install chromium
```

Verificar instalación:

```powershell
python --version
where python
python -m pip -V
```

El `where python` debe apuntar a una ruta similar a:

```text
C:\datoszentrixlatam\ZT-DataEmpresasPriv\.venv\Scripts\python.exe
```

---

### Si Windows bloquea la activación del entorno

Si PowerShell muestra error de permisos al activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

ejecutar una vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Luego cerrar y abrir PowerShell nuevamente, entrar al proyecto y activar:

```powershell
cd C:\datoszentrixlatam\ZT-DataEmpresasPriv
.\.venv\Scripts\Activate.ps1
```

---

### Archivo `.env`

Crear el archivo `.env` en la raíz del proyecto:

```env
SERPER_API_KEY=
TAVILY_API_KEY=
EXA_API_KEY=
```

Las claves reales deben colocarse únicamente en `.env`.

No subir `.env` a GitHub.

---

### Archivo `requirements.txt`

El archivo debe contener como mínimo:

```txt
requests>=2.32.0
pandas>=2.2.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
PyYAML>=6.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
urllib3>=2.0.0
tldextract>=5.1.0
tenacity>=8.2.0
tqdm>=4.66.0
playwright>=1.47.0
```

---

## Comandos principales

```bash
python main.py build-queries --niche leasing_laptops

python main.py search \
  --niche leasing_laptops \
  --limit-queries 2

python main.py companies

python main.py validate-webs

python main.py crawl-seeds

python main.py crawl \
  --limit-companies 2 \
  --max-pages 8

python main.py extract-emails

python main.py clean-emails

python main.py export-final
```

---

## 2 Ejecución resumida diaria

Para una ejecución diaria controlada:

```bash
cd /Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv && source .venv/bin/activate

python main.py build-queries --niche leasing_laptops
python main.py search --niche leasing_laptops --limit-queries 50
python main.py companies && python main.py validate-webs && python main.py crawl-seeds
python main.py crawl --limit-companies 500 --max-pages 8 --delay 0.35
python main.py extract-emails && python main.py clean-emails && python main.py export-final
```

---

## Agregar nuevos nichos

No es necesario borrar los nichos anteriores. Si se desea buscar otro tipo de empresas, se debe agregar un nuevo bloque dentro de:

```text
config/niches.yaml
```

Ejemplo:

```yaml
repuestos_tecnologia:
  enabled: true
  name: "Repuestos y componentes tecnológicos"
  country: "Perú"

  keywords:
    - "venta de repuestos de laptops Perú"
    - "repuestos para laptops empresas Perú"
    - "importador de repuestos de laptops Perú"

  commercial_interest:
    - "repuestos"
    - "pantallas"
    - "teclados"
    - "baterías"
    - "cargadores"
```

Luego se ejecuta solo ese nicho:

```bash
python main.py build-queries --niche repuestos_tecnologia
python main.py search --niche repuestos_tecnologia --limit-queries 50
python main.py companies
python main.py validate-webs
python main.py crawl-seeds
python main.py crawl --limit-companies 500 --max-pages 8
python main.py extract-emails
python main.py clean-emails
python main.py export-final
```

Los nichos anteriores quedan guardados. Si una empresa aparece en más de un nicho, no se duplica; se mantiene una sola empresa por dominio y se agregan sus señales de origen.

---

## Agregar nuevas API keys o proveedores

Los proveedores se configuran en:

```text
config/search_providers.yaml
```

Las API keys se guardan en:

```text
.env
```

Ejemplo de `.env`:

```env
SERPER_API_KEY=
TAVILY_API_KEY=
EXA_API_KEY=
NUEVO_PROVIDER_API_KEY=
```

Ejemplo de `config/search_providers.yaml`:

```yaml
providers:

  serper:
    enabled: true
    priority: 1
    api_key_env: SERPER_API_KEY

  tavily:
    enabled: true
    priority: 2
    api_key_env: TAVILY_API_KEY

  exa:
    enabled: true
    priority: 3
    api_key_env: EXA_API_KEY

  nuevo_provider:
    enabled: true
    priority: 4
    api_key_env: NUEVO_PROVIDER_API_KEY
```

La prioridad define el orden de uso:

```text
1 = primero
2 = segundo
3 = tercero
4 = cuarto
```

Si solo se agrega una nueva API key de un proveedor ya existente, no se modifica el código. Solo se actualiza `.env`.

---

## GitHub + ZIP de estado

El código del proyecto puede estar en GitHub, pero el avance del sistema no siempre se guarda ahí porque normalmente está en `.gitignore`.

GitHub guarda principalmente:

```text
src/
config/
main.py
requirements.txt
documentación .md
```

Pero para no perder el avance se debe respaldar aparte:

```text
data/cache/
data/processed/
data/output/
logs/
```

Crear ZIP de estado:

```bash
zip -r ZT-DataEmpresasPriv_ESTADO.zip \
  data/cache \
  data/processed \
  data/output \
  logs
```

Restaurar en nueva PC:

```bash
git clone URL_DEL_REPOSITORIO
cd ZT-DataEmpresasPriv
unzip RUTA_DEL_ZIP_ESTADO.zip
```

Luego crear nuevamente el entorno virtual y restaurar `.env` manualmente.

Regla rápida:

```text
GitHub = código
ZIP    = cache + logs + outputs
.env   = privado
.venv  = se recrea
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
