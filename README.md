# SIGA-NNH

**Sistema Informático Gestionable y de Acompañamiento de Niñas, Niños y Adolescentes Huérfanos**

Desarrollado por **Worldstrix — Soluciones Tecnológicas Integrales**
Proyecto de la materia *Bases de Datos* · Ciencia de Datos · ESCOM – IPN

---

## ¿De qué trata el proyecto?

SIGA-NNH es una aplicación web para una fundación que acompaña a niñas, niños y
adolescentes (NNA) en situación de orfandad, frecuentemente como consecuencia de
delitos graves. El problema que resuelve: hoy la información de cada menor suele
estar dispersa en expedientes físicos, lo que retrasa trámites y pone en riesgo
datos sensibles.

El sistema **centraliza en una sola base de datos** la información legal, médica,
social, lingüística y geográfica de cada NNA y de sus tutores, de modo que los
equipos de trabajo social, psicología, medicina y derecho trabajen con datos
**precisos, trazables y seguros**.

### Qué incluye

- **Catálogos oficiales** para validar la información:
  - *SEPOMEX* (estados, municipios y asentamientos con código postal).
  - *INALI* (lenguas indígenas, familias y variantes).
  - *OMS / CIE-10* (enfermedades) y *CIF* (discapacidades).
  - *LGDNNA* (catálogo de derechos del Art. 13).
- **Expediente integral del NNA:** alta del menor, Ficha Única de Datos (FUD /
  hecho victimal), idiomas, discapacidades, padecimientos y documentos
  digitalizados.
- **Restitución de derechos:** plan de restitución, derechos vulnerados, medidas
  de protección, instituciones y seguimientos (basado en la *Caja de
  Herramientas* y la LGDNNA).
- **Tutores y equipos multidisciplinarios** (abogado, doctor, psicólogo y
  trabajador social).
- **Privacidad y auditoría:** consentimiento de datos, solicitudes ARCO y
  bitácora de accesos a información sensible.
- **Control de acceso por roles** (director, coordinador, trabajador social,
  abogado, doctor, psicólogo).

---

## Tecnologías

- **Python** + **Django 5.2**
- **PostgreSQL** (motor recomendado; con respaldo automático a SQLite para una
  primera ejecución rápida)
- `openpyxl` (carga de catálogos en Excel) · `python-dotenv` (variables de
  entorno)

---

## Requisitos

- Python 3.11 o superior
- PostgreSQL 14 o superior (recomendado)
- `git`

---

## Instalación

Los comandos son los mismos en cualquier sistema operativo; solo cambian dos
líneas (activar el entorno virtual y copiar el `.env`), que se indican abajo.

```bash
# 1. Clonar el repositorio
git clone https://github.com/cesarGonzalez1/NNABD.git
cd NNABD

# 2. Crear y activar el entorno virtual
python -m venv .venv
#   Windows (PowerShell):   .venv\Scripts\Activate.ps1
#   macOS / Linux:          source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
#   macOS / Linux:  cp .env.example .env
#   Windows:        copy .env.example .env
#   Luego edita .env con los datos de tu PostgreSQL.

# 5. Crear las tablas
python manage.py migrate

# 6. Cargar los catálogos oficiales
python manage.py cargar_sepomex --archivo data/CPdescarga.txt --limpiar
python manage.py cargar_catalogos_nna --archivo "ruta/al/catalogos nna.xlsx"

# 7. Crear el usuario administrador
python manage.py createsuperuser

# 8. Levantar el servidor
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` en el navegador.

---

## Variables de entorno (`.env`)

Copia `.env.example` y ajusta tus valores:

```
DEBUG=True
SECRET_KEY=pon-aqui-una-clave-larga-y-aleatoria
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=siga_nnh
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
```

> Si **no** defines `DB_NAME`, el proyecto usa SQLite automáticamente. Para
> trabajo real y para la entrega se recomienda PostgreSQL.

---

## Estructura del proyecto

```
NNABD/
├── manage.py
├── requirements.txt
├── schema_postgres_5fn.sql     # esquema SQL (PostgreSQL) en 5FN, para el diagrama E-R
├── sigannh/                    # configuración del proyecto Django
│   ├── settings.py
│   └── urls.py
├── web/                        # aplicación principal
│   ├── models.py               # modelo de datos (catálogos, NNA, tutores, FUD…)
│   ├── views.py                # lógica y control de acceso por roles
│   ├── forms.py
│   ├── migrations/             # migraciones (definen la base "desde código")
│   ├── management/commands/    # cargadores de catálogos (SEPOMEX, NNA)
│   └── templates/              # interfaces
└── data/                       # catálogos de referencia (CSV / TXT)
```

---

## Base de datos y diagrama E-R

El archivo `schema_postgres_5fn.sql` contiene el esquema en SQL puro para
PostgreSQL, normalizado hasta la **Quinta Forma Normal**. Para verlo como
diagrama entidad-relación:

```bash
createdb siga_nnh
psql -d siga_nnh -f schema_postgres_5fn.sql
```

Luego, en **pgAdmin** (clic derecho en la base → *ERD For Database*) o en
**DBeaver** (clic derecho en el esquema → *View Diagram*).

---

## Equipo

Worldstrix — Bustamante Villanueva Diego Jehu · González Flores César ·
Pérez Jiménez Emiliano · Tolteca Hernández José Antonio
