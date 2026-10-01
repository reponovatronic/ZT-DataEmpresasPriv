# Ejecución Diaria — 3 Proyectos Zentrix

Objetivo operativo:

```text
Procesar aproximadamente 500 registros por día
```

Proyectos:

```text
1. zt-dataestado
2. dataempsunat
3. ZT-DataEmpresasPriv
```

Este documento está pensado únicamente como recordatorio rápido de ejecución.

---

# 1. ZT-DATAESTADO

Proyecto de instituciones públicas, hospitales, municipalidades, entidades del Estado, etc.

## Paso 1 — Entrar y activar

```bash
cd /RUTA/zt-dataestado
source .venv/bin/activate
```

En Windows:

```powershell
cd C:\RUTA\zt-dataestado
.\.venv\Scripts\Activate.ps1
```

---

## Paso 2 — Procesar lote diario

Usar el comando de búsqueda/carga del proyecto con límite aproximado de:

```text
500 targets
```

Si el proyecto separa búsqueda, validación y crawl, mantener este orden:

```text
BUSCAR / GENERAR TARGETS
        ↓
VALIDAR WEBS
        ↓
GENERAR SEEDS
        ↓
CRAWLEAR PENDIENTES
        ↓
EXTRAER EMAILS
        ↓
LIMPIAR CONTACTOS
        ↓
EXPORTAR EXCEL
```

Regla:

```text
NO borrar cache
NO borrar HTML
NO borrar logs
```

Comprobar al final que los pendientes bajaron y el master aumentó.

---

# 2. DATAEMPSUNAT

Proyecto de empresas privadas provenientes del padrón SUNAT.

## Paso 1 — Entrar y activar

```bash
cd /RUTA/dataempsunat
source .venv/bin/activate
```

Windows:

```powershell
cd C:\RUTA\dataempsunat
.\.venv\Scripts\Activate.ps1
```

---

## Paso 2 — Verificar padrón SUNAT

Antes de iniciar un nuevo padrón:

```text
1. Descargar ZIP oficial de SUNAT.
2. Descomprimir.
3. Colocar la fuente en la carpeta configurada por el proyecto.
4. No reemplazar el cache de búsquedas/contactos.
```

Si el padrón ya está cargado, no volver a descargarlo diariamente.

---

## Paso 3 — Procesar aproximadamente 500 empresas

Orden normal:

```text
PADRÓN SUNAT
    ↓
SELECCIONAR 500 PENDIENTES
    ↓
BUSCAR WEB
    ↓
VALIDAR WEB
    ↓
CRAWLEAR WEB
    ↓
EXTRAER CONTACTOS
    ↓
LIMPIAR / DEDUP
    ↓
EXPORTAR EXCEL
```

Regla diaria:

```text
SOLO pendientes
NO volver a procesar RUC ya terminado
NO borrar cache
```

Al terminar revisar:

```text
RUC procesados
RUC pendientes
webs encontradas
emails encontrados
errores
```

---

# 3. ZT-DATAEMPRESASPRIV

Proyecto de prospección por nichos comerciales.

Ruta típica:

```bash
cd /Users/USUARIO/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv
source .venv/bin/activate
```

Windows:

```powershell
cd C:\datoszentrixlatam\ZT-DataEmpresasPriv
.\.venv\Scripts\Activate.ps1
```

---

## Paso 1 — Generar queries

Solo cuando agregues o modifiques un nicho:

```bash
python main.py build-queries   --niche leasing_laptops
```

No es necesario repetirlo si las queries no cambiaron.

---

## Paso 2 — Ejecutar búsquedas pendientes

Para controlar consumo:

```bash
python main.py search   --niche leasing_laptops   --limit-queries 50
```

Ajusta `--limit-queries` según tu cuota diaria.

Las queries ya procesadas quedan en cache.

---

## Paso 3 — Actualizar empresas

```bash
python main.py companies
```

---

## Paso 4 — Validar solo webs nuevas

```bash
python main.py validate-webs
```

---

## Paso 5 — Generar seeds

```bash
python main.py crawl-seeds
```

---

## Paso 6 — Crawlear lote diario

Para una prueba:

```bash
python main.py crawl   --limit-companies 10   --max-pages 8
```

Para un lote mayor:

```bash
python main.py crawl   --limit-companies 500   --max-pages 8
```

El sistema debe omitir seeds y páginas ya cacheadas.

---

## Paso 7 — Extraer contactos

```bash
python main.py extract-emails
```

---

## Paso 8 — Limpiar

```bash
python main.py clean-emails
```

---

## Paso 9 — Exportar

```bash
python main.py export-final
```

Resultado:

```text
data/output/ZT_DataEmpresasPriv.xlsx
```

---

# 4. Rutina resumida diaria

## ZT-DATAESTADO

```text
activar venv
↓
procesar máximo ~500 pendientes
↓
validar
↓
crawl
↓
extraer contactos
↓
exportar
```

## DATAEMPSUNAT

```text
activar venv
↓
tomar ~500 RUC pendientes
↓
buscar/validar webs
↓
crawl
↓
extraer contactos
↓
exportar
```

## ZT-DATAEMPRESASPRIV

```bash
source .venv/bin/activate

python main.py search   --niche leasing_laptops   --limit-queries 50

python main.py companies

python main.py validate-webs

python main.py crawl-seeds

python main.py crawl   --limit-companies 500   --max-pages 8

python main.py extract-emails

python main.py clean-emails

python main.py export-final
```

---

# 5. Regla diaria para los tres

Antes de empezar:

```text
1. Activar el .venv correcto.
2. Verificar que el proyecto correcto esté abierto.
3. No borrar cache.
4. No borrar logs.
5. No borrar HTML guardado.
6. Ejecutar solo pendientes.
7. Exportar al final.
```

Al terminar:

```text
1. Revisar errores.
2. Revisar cantidad procesada.
3. Revisar contactos encontrados.
4. Revisar Excel final.
5. Hacer backup periódico de cache + logs.
```

---

# 6. Backup rápido diario recomendado

Dentro de cada proyecto:

```bash
zip -r ESTADO_DIARIO.zip   data/cache   data/processed   data/output   logs
```

No incluir `.env`.

---

# 7. Nota sobre 500 por día

El número 500 debe aplicarse sobre registros o empresas pendientes, no sobre registros ya cacheados.

La lógica correcta es:

```text
500 PENDIENTES NUEVOS
```

y no:

```text
primeros 500 del archivo cada día
```

Así el proyecto avanza continuamente y evita gastar APIs o crawlear nuevamente información ya obtenida.



cd /Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv && source .venv/bin/activate
python main.py build-queries --niche leasing_laptops
python main.py search --niche leasing_laptops --limit-queries 50
python main.py companies && python main.py validate-webs && python main.py crawl-seeds
python main.py crawl --limit-companies 500 --max-pages 8 --delay 0.35
python main.py extract-emails && python main.py clean-emails && python main.py export-final

cd /Users/a1234/Desktop/datoszentrixlatam/zt-dataestado && source .venv/bin/activate
python main.py search --limit-targets 500
python main.py validate-webs
python main.py crawl-seeds
python main.py crawl --limit-targets 500 --max-pages 8 --delay 0.35
python main.py extract-emails && python main.py clean-emails && python main.py export-final

cd /Users/a1234/Desktop/datoszentrixlatam/dataempsunat && source .venv/bin/activate
python main.py load-sunat --limit-rows 500
python main.py search-webs --limit-companies 500
python main.py validate-webs
python main.py crawl --limit-companies 500 --max-pages 8 --delay 0.35
python main.py extract-emails && python main.py clean-emails && python main.py export-final


# ============================================================
# 1. ZT-DATAEMPRESASPRIV
# Proyecto: empresas privadas por nicho
# Nicho actual: leasing / renting / alquiler de laptops
# ============================================================

# 1.1 Entrar al proyecto y activar entorno
cd /Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv && source .venv/bin/activate

# 1.2 Generar queries del nicho
python main.py build-queries --niche leasing_laptops

# 1.3 Ejecutar búsquedas pendientes
python main.py search --niche leasing_laptops --limit-queries 50

# 1.4 Detectar empresas, validar webs y generar seeds
python main.py companies && python main.py validate-webs && python main.py crawl-seeds

# 1.5 Crawlear empresas pendientes
python main.py crawl --limit-companies 500 --max-pages 8 --delay 0.35

# 1.6 Extraer contactos, limpiar y exportar Excel final
python main.py extract-emails && python main.py clean-emails && python main.py export-final


# ============================================================
# 2. ZT-DATAESTADO
# Proyecto: entidades públicas, hospitales, municipalidades, etc.
# ============================================================

# 2.1 Entrar al proyecto y activar entorno
cd /Users/a1234/Desktop/datoszentrixlatam/zt-dataestado && source .venv/bin/activate

# 2.2 Ejecutar búsqueda de targets pendientes
python main.py search --limit-targets 500

# 2.3 Validar webs encontradas
python main.py validate-webs

# 2.4 Generar seeds para crawler
python main.py crawl-seeds

# 2.5 Crawlear targets pendientes
python main.py crawl --limit-targets 500 --max-pages 8 --delay 0.35

# 2.6 Extraer contactos, limpiar y exportar Excel final
python main.py extract-emails && python main.py clean-emails && python main.py export-final


# ============================================================
# 3. DATAEMPSUNAT
# Proyecto: empresas privadas desde padrón SUNAT
# ============================================================

# 3.1 Entrar al proyecto y activar entorno
cd /Users/a1234/Desktop/datoszentrixlatam/dataempsunat && source .venv/bin/activate

# 3.2 Cargar lote de empresas desde SUNAT
python main.py load-sunat --limit-rows 500

# 3.3 Buscar webs corporativas de empresas pendientes
python main.py search-webs --limit-companies 500

# 3.4 Validar webs encontradas
python main.py validate-webs

# 3.5 Crawlear empresas pendientes
python main.py crawl --limit-companies 500 --max-pages 8 --delay 0.35

# 3.6 Extraer contactos, limpiar y exportar Excel final
python main.py extract-emails && python main.py clean-emails && python main.py export-final



# ZT-DATAEMPRESASPRIV
/Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv/data/output/ZT_DataEmpresasPriv.xlsx

# ZT-DATAESTADO
/Users/a1234/Desktop/datoszentrixlatam/zt-dataestado/data/output/ZT_DataEstado.xlsx

# DATAEMPSUNAT
/Users/a1234/Desktop/datoszentrixlatam/dataempsunat/data/output/DataEmpSunat.xlsx



| Proyecto | Excel final con correos | CSV final con correos |
|---|---|---|
| Estado | `/Users/a1234/Desktop/datoszentrixlatam/zt-dataestado/data/output/ZT_DataEstado.xlsx` | `/Users/a1234/Desktop/datoszentrixlatam/zt-dataestado/data/output/ZT_DataEstado.csv` |
| SUNAT empresas privadas | `/Users/a1234/Desktop/datoszentrixlatam/dataempsunat/data/output/DataEmpSunat.xlsx` | `/Users/a1234/Desktop/datoszentrixlatam/dataempsunat/data/output/DataEmpSunat.csv` |
| Empresas privadas por nicho | `/Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv/data/output/ZT_DataEmpresasPriv.xlsx` | `/Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv/data/output/ZT_DataEmpresasPriv.csv` |





## Agregar nuevos nichos

No es necesario borrar los nichos anteriores. Si se desea buscar otro tipo de empresas, se debe agregar un nuevo bloque dentro de `config/niches.yaml`.

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


python main.py build-queries --niche repuestos_tecnologia
python main.py search --niche repuestos_tecnologia --limit-queries 50
python main.py companies
python main.py validate-webs
python main.py crawl-seeds
python main.py crawl --limit-companies 500 --max-pages 8
python main.py extract-emails
python main.py clean-emails
python main.py export-final



## Agregar nuevas API keys o proveedores

Los tres proyectos pueden trabajar con varias API keys o proveedores de búsqueda. La regla es:

1. La API key se agrega en el archivo `.env`.
2. El proveedor se configura en `config/search_providers.yaml`.
3. El código usa el proveedor si está habilitado y tiene API key.
4. Si un proveedor falla o no tiene resultados, el sistema puede intentar con el siguiente.

Ejemplo de `.env`:

```env
SERPER_API_KEY=
TAVILY_API_KEY=
EXA_API_KEY=
NUEVO_PROVIDER_API_KEY=


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



cd /Users/a1234/Desktop/datoszentrixlatam/dataempsunat

zip -r dataempsunat_ESTADO.zip \
  data/cache \
  data/raw \
  data/processed \
  data/output \
  logs

cd /Users/a1234/Desktop/datoszentrixlatam/zt-dataestado

zip -r zt-dataestado_ESTADO.zip \
  data/cache \
  data/processed \
  data/output \
  logs

cd /Users/a1234/Desktop/datoszentrixlatam/ZT-DataEmpresasPriv

zip -r ZT-DataEmpresasPriv_ESTADO.zip \
  data/cache \
  data/processed \
  data/output \
  logs