# Mantenimiento y Migración — ZT-DataEmpresasPriv

## 1. Regla principal

La parte más importante del proyecto es:

```text
data/cache/
```

porque contiene el estado incremental.

También deben respaldarse:

```text
data/processed/
data/output/
logs/
config/
src/
main.py
requirements.txt
```

---

# 2. No migrar

No copiar:

```text
.venv/
__pycache__/
*.pyc
.DS_Store
```

El entorno virtual se recrea en cada equipo.

---

# 3. El archivo .env

`.env` contiene credenciales.

No incluirlo en ZIP compartidos ni repositorios.

Debe transferirse separadamente y de forma privada.

---

# 4. Backup completo en macOS

Desde el directorio padre:

```bash
cd /Users/USUARIO/Desktop/datoszentrixlatam
```

Crear ZIP:

```bash
zip -r ZT-DataEmpresasPriv_BACKUP.zip   ZT-DataEmpresasPriv   -x "ZT-DataEmpresasPriv/.venv/*"      "ZT-DataEmpresasPriv/**/__pycache__/*"      "ZT-DataEmpresasPriv/*.pyc"      "ZT-DataEmpresasPriv/**/.DS_Store"      "ZT-DataEmpresasPriv/.env"
```

Este ZIP debe contener:

```text
src/
config/
data/cache/
data/processed/
data/output/
logs/
main.py
requirements.txt
documentación
```

---

# 5. Verificar ZIP en Mac

```bash
unzip -l ZT-DataEmpresasPriv_BACKUP.zip | head -50
```

Verificar cache:

```bash
unzip -l ZT-DataEmpresasPriv_BACKUP.zip | grep "data/cache" | head
```

Verificar logs:

```bash
unzip -l ZT-DataEmpresasPriv_BACKUP.zip | grep "logs/" | head
```

---

# 6. Migración Mac → Windows

## Paso 1

Copiar:

```text
ZT-DataEmpresasPriv_BACKUP.zip
```

al equipo Windows.

## Paso 2

Descomprimir:

```powershell
Expand-Archive `
  -Path .\ZT-DataEmpresasPriv_BACKUP.zip `
  -DestinationPath C:\datoszentrixlatam `
  -Force
```

## Paso 3

Entrar:

```powershell
cd C:\datoszentrixlatam\ZT-DataEmpresasPriv
```

## Paso 4

Crear nuevo entorno:

```powershell
python -m venv .venv
```

## Paso 5

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Paso 6

Instalar:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Paso 7

Crear/restaurar `.env` de forma privada.

## Paso 8

Verificar:

```powershell
python main.py --help
```

---

# 7. Migración Windows → Mac

## Paso 1

Crear ZIP en Windows sin `.venv` ni `.env`.

Ejemplo PowerShell:

```powershell
$src = "C:\datoszentrixlatam\ZT-DataEmpresasPriv"
$tmp = "C:\Temp\ZT-DataEmpresasPriv"

Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $tmp | Out-Null

robocopy $src $tmp /E `
  /XD ".venv" "__pycache__" `
  /XF ".env" "*.pyc" ".DS_Store"

Compress-Archive `
  -Path $tmp `
  -DestinationPath C:\Temp\ZT-DataEmpresasPriv_BACKUP.zip `
  -Force
```

## Paso 2

Copiar el ZIP al Mac.

## Paso 3

Descomprimir:

```bash
cd ~/Desktop/datoszentrixlatam
unzip ~/Downloads/ZT-DataEmpresasPriv_BACKUP.zip
```

## Paso 4

Entrar:

```bash
cd ZT-DataEmpresasPriv
```

## Paso 5

Crear entorno nuevo:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

## Paso 6

Instalar:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Paso 7

Restaurar `.env`.

---

# 8. Verificar que el cache llegó

```bash
ls -lh data/cache/
```

HTML:

```bash
find data/cache/html -type f | wc -l
```

Empresas:

```bash
wc -l data/cache/companies_master.csv
```

Resultados:

```bash
wc -l data/cache/search_results.csv
```

Páginas:

```bash
wc -l data/cache/crawled_pages.csv
```

Emails:

```bash
wc -l data/cache/emails_found.csv
```

---

# 9. Backup solo del estado incremental

Si solo quieres respaldar datos, cache y logs:

```bash
zip -r ZT_DataEmpresasPriv_ESTADO.zip   data/cache   data/processed   data/output   logs
```

Esto es útil antes de cambios grandes.

---

# 10. Antes de actualizar código

Crear respaldo:

```bash
cp -R data/cache   data/cache_backup_$(date +%Y%m%d_%H%M%S)
```

O usar ZIP.

---

# 11. Reinstalar entorno virtual

Si `.venv` falla:

```bash
deactivate 2>/dev/null || true
rm -rf .venv

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

No borrar:

```text
data/cache/
```

---

# 12. Mantenimiento de Playwright

Si Chromium falta:

```bash
python -m playwright install chromium
```

---

# 13. Cambiar API key

Editar:

```text
.env
```

No cambiar código.

---

# 14. Cambiar proveedores

Editar:

```text
config/search_providers.yaml
```

---

# 15. Agregar nicho

Editar:

```text
config/niches.yaml
```

Después:

```bash
python main.py build-queries   --niche NOMBRE_NICHO
```

---

# 16. Orden correcto de migración

```text
1. Detener ejecución.
2. Crear ZIP.
3. Verificar que ZIP incluya cache y logs.
4. Copiar ZIP.
5. Descomprimir en nuevo equipo.
6. Crear nuevo .venv.
7. Instalar requirements.
8. Instalar Chromium.
9. Restaurar .env.
10. Verificar cache.
11. Ejecutar prueba pequeña.
12. Continuar desde donde quedó.
```
