# Catalogos base

Estos CSV son la version controlada del archivo `catalogos nna.xlsx`
proporcionado por el profesor.

La migracion `0011_seed_catalogos_profesor` carga:

- modos de adquisicion de lengua
- tipos de contacto
- familias linguisticas
- lenguas
- tipos de discapacidad
- niveles de competencia oral

SEPOMEX se mantiene separado para domicilios:

```powershell
python manage.py cargar_sepomex --archivo CPdescarga.txt
```

Se puede recargar con:

```powershell
python manage.py cargar_catalogos_nna --archivo "C:\ruta\catalogos nna.xlsx"
```
