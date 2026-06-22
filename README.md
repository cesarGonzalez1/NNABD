# NNABD en Postgresql

## 1. Instalar PostgreSQL

Instala PostgreSQL para Windows desde el instalador oficial. Durante la instalacion guarda la contrasena del usuario `postgres`.

## 2. Crear usuario y base

Abre SQL Shell (`psql`) o pgAdmin y ejecuta:

```sql
CREATE USER nnabd_user WITH PASSWORD 'cambia-esta-contrasena';
CREATE DATABASE nnabd OWNER nnabd_user;
ALTER ROLE nnabd_user SET client_encoding TO 'utf8';
ALTER ROLE nnabd_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE nnabd_user SET timezone TO 'America/Mexico_City';
GRANT ALL PRIVILEGES ON DATABASE nnabd TO nnabd_user;
```

## 3. Configurar el proyecto

Copia `.env.example` a `.env` y ajusta `DB_PASSWORD`.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## 4. Cargar catalogos

```powershell
python manage.py cargar_sepomex --archivo data\CPdescarga.txt --limpiar
python manage.py cargar_catalogos --dir data\catalogos --limpiar-todo
```

SEPOMEX se usa para domicilios. El archivo `catalogos` del profesor se usa para modos de adquisicion de lengua, tipos de contacto, familias linguisticas, lenguas, tipos de discapacidad y niveles de competencia oral.

Los CSV de referencia inicial estan en `data\catalogos\` y se cargan con las migraciones. Si el profesor actualiza el Excel, vuelve a ejecutar `cargar_catalogos`.

## 5. Validar

```powershell
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
```

`settings.py` usa SQLite automaticamente cuando no existe `DB_NAME` en `.env`, para que las pruebas y una primera revision no fallen antes de instalar PostgreSQL. En desarrollo real con Windows usa `.env` con PostgreSQL.
