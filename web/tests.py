import tempfile
from datetime import date
from io import StringIO

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import NNAForm
from .models import (
    Asentamiento,
    BitacoraAcceso,
    CapituloEnfermedad,
    ContactoNNA,
    Derecho,
    DerechoVulnerado,
    Discapacidad,
    DiscapacidadNNA,
    Domicilio,
    Empleado,
    Enfermedad,
    EntidadFederativa,
    EquipoMultidisciplinario,
    FamiliaLinguistica,
    HechoVictimal,
    IdiomaEmpleado,
    IdiomaNNA,
    IdiomaTutor,
    Lengua,
    ModoAdquisicionLengua,
    Municipio,
    NNA,
    NNATutor,
    Nacionalidad,
    NivelCompetenciaOral,
    PadecimientoNNA,
    PlanRestitucion,
    Sexo,
    TipoAsentamiento,
    TipoContacto,
    TipoDiscapacidad,
    Tutor,
)


@override_settings(SECURE_SSL_REDIRECT=False)
class NNABDPlanTests(TestCase):
    def crear_empleado(self, idx, rol):
        user = User.objects.create_user(
            username=f"user{idx}",
            password="pass",
        )
        empleado = Empleado.objects.create(
            usuario=user,
            nombre=f"Nombre{idx}",
            apellido_paterno="Prueba",
            apellido_materno="",
            rfc=f"RFC{idx:010d}",
            curp=f"CURP{idx:014d}",
            fecha_nacimiento=date(1990, 1, 1),
            tipo_trabajador="empleado",
            rol=rol,
        )
        return user, empleado

    def crear_domicilio(self, idx=1):
        entidad = EntidadFederativa.objects.create(
            clave=f"{idx:02d}",
            nombre=f"Estado {idx}",
            abreviatura=f"E{idx}",
        )
        municipio = Municipio.objects.create(
            entidad=entidad,
            clave=f"{idx:03d}",
            nombre=f"Municipio {idx}",
        )
        tipo = TipoAsentamiento.objects.create(nombre=f"Colonia {idx}")
        asentamiento = Asentamiento.objects.create(
            municipio=municipio,
            tipo_asentamiento=tipo,
            nombre=f"Centro {idx}",
            codigo_postal=f"{idx:05d}",
        )
        return Domicilio.objects.create(
            asentamiento=asentamiento,
            calle=f"Calle {idx}",
            numero_exterior=str(idx),
        )

    def crear_nna(self, empleado):
        return NNA.objects.create(
            nombre="Ana",
            apellido_paterno="Lopez",
            apellido_materno="",
            fecha_nacimiento=date(2015, 5, 10),
            fecha_ingreso=date(2026, 1, 15),
            registrado_por=empleado,
        )

    def formset_management(self, prefix, total):
        return {
            f"{prefix}-TOTAL_FORMS": str(total),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }

    def test_non_director_cannot_manage_employee_access(self):
        user, _ = self.crear_empleado(1, "analista")
        _, target = self.crear_empleado(2, "trabajador_social")
        self.client.force_login(user)

        protected_urls = [
            reverse("consultar_empleado", args=[target.id]),
            reverse("editar_empleado", args=[target.id]),
            reverse("eliminar_persona", args=[target.id]),
            reverse("revocar_acceso", args=[target.id]),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)

    def test_sepomez_import_is_idempotent_and_skips_legal_header(self):
        sample = "\n".join([
            "Texto legal de Correos de Mexico",
            "d_codigo|d_asenta|d_tipo_asenta|D_mnpio|d_estado|d_ciudad|d_CP|c_estado|c_oficina|c_CP|c_tipo_asenta|c_mnpio|id_asenta_cpcons|d_zona|c_cve_ciudad",
            "01000|San Angel|Colonia|Alvaro Obregon|Ciudad de Mexico|Ciudad de Mexico|01001|09|01001||09|010|0001|Urbano|01",
            "01000|San Angel Inn|Colonia|Alvaro Obregon|Ciudad de Mexico|Ciudad de Mexico|01001|09|01001||09|010|0002|Urbano|01",
        ])
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as fh:
            fh.write(sample)
            path = fh.name

        out = StringIO()
        call_command("cargar_sepomex", archivo=path, stdout=out, stderr=StringIO())
        call_command("cargar_sepomex", archivo=path, stdout=out, stderr=StringIO())

        self.assertEqual(EntidadFederativa.objects.count(), 1)
        self.assertEqual(Municipio.objects.count(), 1)
        self.assertEqual(Asentamiento.objects.count(), 2)

    def test_crear_nna_reuses_tutor_address_and_bridge_table(self):
        user, empleado = self.crear_empleado(3, "trabajador_social")
        domicilio = self.crear_domicilio()
        tutor = Tutor.objects.create(
            nombre="Maria",
            apellido_paterno="Gomez",
            parentesco_con_nna="abuela",
            domicilio=domicilio,
        )
        self.client.force_login(user)

        post_data = {
            "folio_nna": "",
            "nombre": "Luis",
            "apellido_paterno": "Gomez",
            "apellido_materno": "",
            "fecha_nacimiento": "2016-03-04",
            "curp": "",
            "escolaridad": "primaria",
            "nombre_escuela": "",
            "lugar_nacimiento_estado": "",
            "lugar_nacimiento_municipio": "",
            "pais_origen": "",
            "condicion_migratoria": "ninguna",
            "pais_destino": "",
            "comunidad_indigena": "",
            "lengua_interprete": "",
            "vive_con_tutor": "on",
            "tutor": str(tutor.id),
            "equipo": "",
            "estatus": "activo",
            "fecha_ingreso": "2026-02-01",
            "observaciones_generales": "",
        }
        post_data.update(self.formset_management("idiomas", 0))
        post_data.update(self.formset_management("discapacidades", 0))
        post_data.update(self.formset_management("padecimientos", 0))

        response = self.client.post(reverse("crear_nna"), post_data)

        self.assertEqual(response.status_code, 302)
        nna = NNA.objects.get(nombre="Luis")
        self.assertEqual(nna.domicilio, domicilio)
        self.assertTrue(nna.folio_nna.startswith("NNA-"))
        self.assertTrue(
            NNATutor.objects.filter(nna=nna, tutor=tutor, principal=True).exists()
        )
        self.assertEqual(nna.registrado_por, empleado)

    def test_nna_form_requires_origin_country_for_foreign_nna(self):
        form = NNAForm(data={
            "nombre": "Nina",
            "apellido_paterno": "Perez",
            "apellido_materno": "",
            "fecha_nacimiento": "2017-01-01",
            "curp": "",
            "escolaridad": "",
            "nombre_escuela": "",
            "lugar_nacimiento_estado": "",
            "lugar_nacimiento_municipio": "",
            "es_extranjero": "on",
            "pais_origen": "",
            "condicion_migratoria": "ninguna",
            "pais_destino": "",
            "comunidad_indigena": "",
            "lengua_interprete": "",
            "vive_con_tutor": "on",
            "tutor": "",
            "equipo": "",
            "estatus": "activo",
            "fecha_ingreso": "2026-01-01",
            "observaciones_generales": "",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("pais_origen", form.errors)

    def test_detalle_nna_registers_consultation_in_bitacora(self):
        user, empleado = self.crear_empleado(4, "trabajador_social")
        nna = self.crear_nna(empleado)
        self.client.force_login(user)
        before = BitacoraAcceso.objects.filter(accion="consulta", nna=nna).count()

        response = self.client.get(reverse("detalle_nna", args=[nna.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            BitacoraAcceso.objects.filter(accion="consulta", nna=nna).count(),
            before + 1,
        )

    def test_edit_expediente_creates_fud_catalog_relations_and_plan_right(self):
        user, empleado = self.crear_empleado(5, "trabajador_social")
        nna = self.crear_nna(empleado)
        tipo_contacto = TipoContacto.objects.get(clave="2")
        lengua = Lengua.objects.get(clave_inali="PROF-001")
        nivel = NivelCompetenciaOral.objects.get(clave="1")
        modo = ModoAdquisicionLengua.objects.get(clave="1")
        tipo_discapacidad = TipoDiscapacidad.objects.get(clave_inegi="1")
        discapacidad = Discapacidad.objects.get(tipo=tipo_discapacidad)
        enfermedad = Enfermedad.objects.get(codigo_cie10="R51")
        derecho = Derecho.objects.get(clave="IX")
        self.client.force_login(user)

        post_data = {
            "fud-tipo_delito": "homicidio",
            "fud-descripcion_delito": "Hecho registrado en FUD.",
            "fud-nombre_victima_directa": "Madre",
            "fud-parentesco_victima_nna": "Madre",
            "fud-estatus_juridico": "denuncia_presentada",
            "plan-folio": "PR-TEST-001",
            "plan-fecha_apertura": "2026-03-01",
            "plan-equipo": "",
            "plan-grado_peligro": "medio",
            "plan-grado_coercion": "baja",
            "plan-diagnostico_general": "Diagnostico inicial.",
            "plan-determinacion_interes_superior": "Determinacion inicial.",
            "plan-estatus": "diagnostico",
            "plan-vigente": "on",
        }
        post_data.update(self.formset_management("contactos", 1))
        post_data.update({
            "contactos-0-tipo": str(tipo_contacto.id),
            "contactos-0-valor": "5551234567",
            "contactos-0-descripcion": "Tutor",
            "contactos-0-principal": "on",
        })
        post_data.update(self.formset_management("idiomas", 1))
        post_data.update({
            "idiomas-0-lengua": str(lengua.id),
            "idiomas-0-nivel": "basico",
            "idiomas-0-nivel_competencia": str(nivel.id),
            "idiomas-0-modo_adquisicion": str(modo.id),
            "idiomas-0-es_lengua_materna": "on",
            "idiomas-0-preferente": "on",
            "idiomas-0-autodenominacion": "Espanol",
        })
        post_data.update(self.formset_management("discapacidades", 1))
        post_data.update({
            "discapacidades-0-tipo": str(tipo_discapacidad.id),
            "discapacidades-0-discapacidad": str(discapacidad.id),
            "discapacidades-0-descripcion_especifica": "Apoyo temporal",
            "discapacidades-0-grado_dependencia": "leve",
            "discapacidades-0-causa": "desconocida",
        })
        post_data.update(self.formset_management("padecimientos", 1))
        post_data.update({
            "padecimientos-0-enfermedad": str(enfermedad.id),
            "padecimientos-0-fecha_diagnostico": "",
            "padecimientos-0-medicamentos": "",
            "padecimientos-0-observaciones_medicas": "",
        })
        post_data.update(self.formset_management("documentos", 1))
        post_data.update({
            "documentos-0-tipo": "fud",
            "documentos-0-nombre_archivo": "FUD inicial",
            "documentos-0-descripcion": "Captura inicial",
            "documentos-0-fecha_documento": "2026-03-01",
        })
        post_data.update(self.formset_management("derechos", 1))
        post_data.update({
            "derechos-0-derecho": str(derecho.id),
            "derechos-0-grado": "vulnerado",
            "derechos-0-descripcion": "Requiere atencion de salud.",
        })

        response = self.client.post(
            reverse("editar_expediente_nna", args=[nna.id]),
            post_data,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(HechoVictimal.objects.filter(nna=nna).exists())
        self.assertTrue(ContactoNNA.objects.filter(nna=nna, tipo=tipo_contacto).exists())
        self.assertTrue(IdiomaNNA.objects.filter(nna=nna, lengua=lengua).exists())
        self.assertTrue(DiscapacidadNNA.objects.filter(nna=nna, discapacidad=discapacidad).exists())
        # Un trabajador social no puede crear diagnósticos mediante un POST manipulado.
        self.assertFalse(PadecimientoNNA.objects.filter(nna=nna, enfermedad=enfermedad).exists())
        plan = PlanRestitucion.objects.get(nna=nna, vigente=True)
        self.assertTrue(DerechoVulnerado.objects.filter(plan=plan, derecho=derecho).exists())
        self.assertEqual(plan.elaborado_por, empleado)

    def test_doctor_can_register_multiple_diagnoses_with_treatment(self):
        trabajador_user, trabajador = self.crear_empleado(20, "trabajador_social")
        doctor_user, doctor = self.crear_empleado(21, "doctor")
        _, abogado = self.crear_empleado(22, "abogado")
        _, psicologo = self.crear_empleado(23, "psicologo")
        equipo = EquipoMultidisciplinario.objects.create(
            nombre="Equipo clinico",
            abogado=abogado,
            doctor=doctor,
            trabajador_social=trabajador,
            psicologo=psicologo,
        )
        nna = self.crear_nna(trabajador)
        nna.equipo = equipo
        nna.save()
        enfermedades = list(Enfermedad.objects.all()[:2])
        self.client.force_login(doctor_user)

        post_data = {}
        for prefix in ("contactos", "idiomas", "discapacidades", "documentos"):
            post_data.update(self.formset_management(prefix, 0))
        post_data.update(self.formset_management("padecimientos", 2))
        for index, enfermedad in enumerate(enfermedades):
            post_data.update({
                f"padecimientos-{index}-enfermedad": str(enfermedad.id),
                f"padecimientos-{index}-fecha_diagnostico": "2026-06-20",
                f"padecimientos-{index}-diagnostico_medico": f"Diagnóstico {index + 1}",
                f"padecimientos-{index}-bajo_tratamiento": "on",
                f"padecimientos-{index}-requiere_medicamento": "on",
                f"padecimientos-{index}-estado_tratamiento": "activo",
                f"padecimientos-{index}-medicamentos": "Tratamiento indicado",
                f"padecimientos-{index}-observaciones_medicas": "Seguimiento médico",
            })

        response = self.client.post(
            reverse("editar_expediente_nna", args=[nna.id]), post_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PadecimientoNNA.objects.filter(nna=nna).count(), 2)
        self.assertFalse(
            PadecimientoNNA.objects.filter(nna=nna).exclude(diagnosticado_por=doctor).exists()
        )
        self.client.force_login(trabajador_user)
        response = self.client.get(reverse("detalle_nna", args=[nna.id]))
        self.assertNotContains(response, "Diagnósticos médicos")

    def test_languages_are_recorded_for_nna_tutor_and_employee(self):
        _, empleado = self.crear_empleado(24, "trabajador_social")
        tutor = Tutor.objects.create(
            nombre="Maria", apellido_paterno="Lopez", parentesco_con_nna="abuela"
        )
        nna = self.crear_nna(empleado)
        lenguas = list(Lengua.objects.all()[:2])

        IdiomaEmpleado.objects.create(
            empleado=empleado, lengua=lenguas[0], nivel="avanzado"
        )
        IdiomaTutor.objects.create(
            tutor=tutor, lengua=lenguas[0], nivel="nativo", preferente=True
        )
        for lengua in lenguas:
            IdiomaNNA.objects.create(nna=nna, lengua=lengua, nivel="intermedio")

        self.assertEqual(empleado.idiomas.count(), 1)
        self.assertEqual(tutor.idiomas.count(), 1)
        self.assertTrue(nna.es_multilingue)

    def test_new_language_and_process_fields_render_in_authorized_forms(self):
        director_user, _ = self.crear_empleado(25, "director")
        self.client.force_login(director_user)
        response = self.client.get(reverse("crear_empleado"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "idiomas-TOTAL_FORMS")

        trabajador_user, _ = self.crear_empleado(26, "trabajador_social")
        self.client.force_login(trabajador_user)
        response = self.client.get(reverse("crear_tutor"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "idiomas-TOTAL_FORMS")

        response = self.client.get(reverse("crear_nna"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "id_nombre_preferido")
        self.assertContains(response, "id_estatus_proceso")
        self.assertNotContains(response, "Enfermedades / Padecimientos")

    def test_plan_links_derechos_vulnerados(self):
        _, empleado = self.crear_empleado(6, "trabajador_social")
        nna = self.crear_nna(empleado)
        plan = PlanRestitucion.objects.create(
            nna=nna,
            folio="PR-TEST-002",
            fecha_apertura=date(2026, 4, 1),
            elaborado_por=empleado,
            grado_peligro="alto",
            grado_coercion="media",
        )
        derecho = DerechoVulnerado.objects.create(
            plan=plan,
            derecho=Derecho.objects.get(clave="XI"),
            grado="vulnerado",
            descripcion="Reincorporacion escolar.",
        )

        self.assertEqual(derecho.plan, plan)
        self.assertEqual(plan.derechos_vulnerados.count(), 1)

    def test_admin_registers_base_catalogs_and_bridge_tables(self):
        expected_models = [
            Sexo, Nacionalidad, TipoContacto, NivelCompetenciaOral,
            ModoAdquisicionLengua, FamiliaLinguistica,
            Lengua, TipoDiscapacidad, Discapacidad,
            CapituloEnfermedad, Enfermedad, NNATutor, ContactoNNA,
            IdiomaNNA, IdiomaTutor, IdiomaEmpleado,
            DiscapacidadNNA, PadecimientoNNA,
        ]
        for model in expected_models:
            self.assertTrue(admin.site.is_registered(model), model.__name__)

        self.assertTrue(Sexo.objects.filter(clave="F").exists())
        self.assertTrue(Nacionalidad.objects.filter(clave="MEX").exists())
        self.assertTrue(Lengua.objects.filter(clave_inali="PROF-001").exists())
        self.assertEqual(Lengua.objects.exclude(catalogo_id__isnull=True).count(), 73)
