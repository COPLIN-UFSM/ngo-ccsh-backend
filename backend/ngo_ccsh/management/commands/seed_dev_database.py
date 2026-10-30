import csv
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, models, transaction
from tqdm import tqdm

from despesas.models import (
    Finalidade,
    GrupoFinalidade,
    Natureza,
    TipoDocumento,
    TipoDocumentoParaFinalidade,
    TipoMovimento,
)
from entidades.models import (
    Cargo,
    Centro,
    CentroSIE,
    Curso,
    Discente,
    Pessoa,
    PessoaSIE,
    Servidor,
    SituacaoUnidade,
    TipoUnidade,
    Unidade,
    UnidadeSIE,
)


LEGACY_MOVEMENTS = {
    36: TipoMovimento.Codigo.REFORCO_EMPENHO,
    37: TipoMovimento.Codigo.REFORCO_EMPENHO,
    **{
        legacy_id: TipoMovimento.Codigo.DISTRIBUICAO
        for legacy_id in range(39, 45)
    },
}


def mapear_unidade_pai(rows):
    """Map each unit to its nearest existing ancestor in the same internal center."""
    by_code = {}
    for row in rows:
        code = row["COD_ESTRUTURADO"]
        if code in by_code:
            raise ValueError(f"Código estruturado duplicado: {code}.")
        parts = code.split(".")
        if (
            len(parts) != 6
            or tuple(map(len, parts)) != (2, 2, 2, 2, 1, 1)
            or any(not part.isdigit() for part in parts)
        ):
            raise ValueError(f"Código estruturado inválido: {code}.")
        by_code[code] = row

    parent_ids = {}
    for row in rows:
        parts = row["COD_ESTRUTURADO"].split(".")
        parent_id = None
        for index in range(len(parts) - 1, -1, -1):
            if not any(character != "0" for character in parts[index]):
                continue
            ancestor = parts[:index] + ["0" * len(part) for part in parts[index:]]
            candidate = by_code.get(".".join(ancestor))
            if candidate is None:
                continue
            if candidate["ID_CENTRO_INTERNO"] == row["ID_CENTRO_INTERNO"]:
                parent_id = int(candidate["ID_UNIDADE_INTERNA"])
            break
        parent_ids[int(row["ID_UNIDADE_INTERNA"])] = parent_id
    return parent_ids


class Command(BaseCommand):
    help = "Carrega dados CSV e converte os catálogos legados para os modelos atuais."

    @staticmethod
    def convert_value(field, value):
        if value == "":
            return None
        if isinstance(field, models.BooleanField):
            return value.strip().upper() in ("TRUE", "1", "YES")
        if isinstance(
            field,
            (models.IntegerField, models.AutoField, models.BigIntegerField),
        ) or field.is_relation:
            return int(value)
        if isinstance(field, models.DecimalField):
            return Decimal(value)
        return value

    @classmethod
    def row_to_model_data(cls, model, row, ignored_columns=()):
        column_map = {
            field.column.upper(): field
            for field in model._meta.local_fields
            if field.column is not None
        }
        data = {}
        for column, value in row.items():
            field = column_map.get(column.upper())
            if field is None:
                if column.lower() in ignored_columns:
                    continue
                raise CommandError(
                    f"A coluna {column!r} não corresponde a um campo de {model.__name__}."
                )
            data[field.attname] = cls.convert_value(field, value)
        return data

    def read_csv(self, path):
        try:
            with path.open(newline="", encoding="utf-8-sig") as file:
                return list(csv.DictReader(file))
        except OSError as exc:
            raise CommandError(f"Não foi possível ler {path}: {exc}") from exc

    def load_model_csv(self, csv_path, filename, model):
        rows = self.read_csv(csv_path / filename)
        for row in rows:
            data = self.row_to_model_data(model, row)
            pk_name = model._meta.pk.attname
            pk = data.pop(pk_name)
            model._base_manager.update_or_create(pk=pk, defaults=data)
        return len(rows)

    def load_units(self, csv_path):
        rows = self.read_csv(csv_path / "UNIDADES.csv")
        try:
            parent_ids = mapear_unidade_pai(rows)
        except (KeyError, ValueError) as exc:
            raise CommandError(f"Não foi possível montar a hierarquia: {exc}") from exc

        pending = {int(row["ID_UNIDADE_INTERNA"]): row for row in rows}
        inserted = set()
        while pending:
            ready = [
                (unit_id, row)
                for unit_id, row in pending.items()
                if parent_ids[unit_id] is None
                or parent_ids[unit_id] in inserted
            ]
            if not ready:
                raise CommandError(
                    "A hierarquia de unidades contém pai ausente ou ciclo."
                )

            for unit_id, row in ready:
                data = self.row_to_model_data(
                    Unidade,
                    row,
                    ignored_columns=("pode_empenhar",),
                )
                data["unidade_pai_id"] = parent_ids[unit_id]
                data.pop("id_unidade_interna")
                Unidade._base_manager.update_or_create(pk=unit_id, defaults=data)
                inserted.add(unit_id)
                del pending[unit_id]
        return len(rows), sum(parent_id is not None for parent_id in parent_ids.values())

    def load_naturezas(self, csv_path):
        rows = self.read_csv(csv_path / "NATUREZAS_FINALIDADES.csv")
        for row in rows:
            Natureza.objects.update_or_create(
                pk=int(row["ID_NATUREZA_FINALIDADE"]),
                defaults={
                    "nome": row["NATUREZA_FINALIDADE"],
                    "ativo": self.convert_value(
                        models.BooleanField(), row["ATIVO"]
                    ),
                },
            )
        return len(rows)

    def load_grupos(self, csv_path):
        rows = self.read_csv(csv_path / "GRUPOS_FINALIDADES.csv")
        for row in rows:
            GrupoFinalidade.objects.update_or_create(
                pk=int(row["ID_GRUPO_FINALIDADE"]),
                defaults={
                    "nome": row["GRUPO_FINALIDADE"],
                    "ativo": self.convert_value(
                        models.BooleanField(), row["ATIVO"]
                    ),
                },
            )
        return len(rows)

    def load_finalidades(self, csv_path):
        rows = self.read_csv(csv_path / "FINALIDADES.csv")
        loaded = 0
        for row in rows:
            legacy_id = int(row["ID_FINALIDADE"])
            legacy_type = int(row["ID_TIPO_FINALIDADE"])
            if legacy_id in LEGACY_MOVEMENTS:
                expected_type = LEGACY_MOVEMENTS[legacy_id]
                if legacy_type != 1 and legacy_id in (36, 37):
                    raise CommandError(
                        f"Finalidade legada {legacy_id} deveria ser reforço de empenho."
                    )
                if legacy_type != 3 and legacy_id >= 39:
                    raise CommandError(
                        f"Finalidade legada {legacy_id} deveria ser transferência."
                    )
                TipoMovimento.obter(expected_type)
                continue

            if legacy_type != 2:
                raise CommandError(
                    f"A finalidade legada {legacy_id} tem tipo não mapeado {legacy_type}."
                )
            Natureza.objects.get(pk=int(row["ID_NATUREZA_FINALIDADE"]))
            grupo_id = row["ID_GRUPO_FINALIDADE"] or None
            if grupo_id:
                GrupoFinalidade.objects.get(pk=int(grupo_id))
            Finalidade.objects.update_or_create(
                pk=legacy_id,
                defaults={
                    "natureza_id": int(row["ID_NATUREZA_FINALIDADE"]),
                    "grupo_id": int(grupo_id) if grupo_id else None,
                    "nome": row["FINALIDADE"],
                    "ativo": self.convert_value(models.BooleanField(), row["ATIVO"]),
                    "permite_transporte": False,
                },
            )
            loaded += 1
        return loaded

    def load_document_types(self, csv_path):
        rows = self.read_csv(csv_path / "TIPOS_DOCUMENTOS.csv")
        loaded = 0
        for row in rows:
            if row["TIPO_DOCUMENTO"].strip().casefold() == "lista siafi":
                continue
            TipoDocumento.objects.update_or_create(
                pk=int(row["ID_TIPO_DOCUMENTO"]),
                defaults={
                    "nome": row["TIPO_DOCUMENTO"],
                    "ativo": self.convert_value(models.BooleanField(), row["ATIVO"]),
                },
            )
            loaded += 1
        return loaded

    def load_document_links(self, csv_path):
        rows = self.read_csv(csv_path / "TIPOS_DOCUMENTOS_PARA_FINALIDADES.csv")
        loaded = 0
        for row in rows:
            if int(row["ID_TIPO_DOCUMENTO"]) == 2:
                continue
            TipoDocumentoParaFinalidade.objects.update_or_create(
                tipo_documento_id=int(row["ID_TIPO_DOCUMENTO"]),
                finalidade_id=int(row["ID_FINALIDADE"]),
                defaults={
                    "obrigatorio": self.convert_value(
                        models.BooleanField(), row["OBRIGATORIO"]
                    ),
                    "ativo": True,
                },
            )
            loaded += 1
        return loaded

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if connection.vendor != "sqlite":
            raise CommandError(
                "Este seed é exclusivo do banco SQLite de desenvolvimento."
            )

        csv_path = Path(settings.BASE_DIR) / "database" / "csv"
        loaders = [
            ("V_CENTROS_SIE.csv", lambda: self.load_model_csv(csv_path, "V_CENTROS_SIE.csv", CentroSIE)),
            ("CENTROS.csv", lambda: self.load_model_csv(csv_path, "CENTROS.csv", Centro)),
            ("V_TIPOS_UNIDADES.csv", lambda: self.load_model_csv(csv_path, "V_TIPOS_UNIDADES.csv", TipoUnidade)),
            ("V_SITUACOES_UNIDADES.csv", lambda: self.load_model_csv(csv_path, "V_SITUACOES_UNIDADES.csv", SituacaoUnidade)),
            ("V_UNIDADES_SIE.csv", lambda: self.load_model_csv(csv_path, "V_UNIDADES_SIE.csv", UnidadeSIE)),
            ("UNIDADES.csv", lambda: self.load_units(csv_path)[0]),
            ("V_CURSOS.csv", lambda: self.load_model_csv(csv_path, "V_CURSOS.csv", Curso)),
            ("V_CARGOS.csv", lambda: self.load_model_csv(csv_path, "V_CARGOS.csv", Cargo)),
            ("V_PESSOAS_SIE.csv", lambda: self.load_model_csv(csv_path, "V_PESSOAS_SIE.csv", PessoaSIE)),
            ("PESSOAS.csv", lambda: self.load_model_csv(csv_path, "PESSOAS.csv", Pessoa)),
            ("V_SERVIDORES.csv", lambda: self.load_model_csv(csv_path, "V_SERVIDORES.csv", Servidor)),
            ("V_DISCENTES.csv", lambda: self.load_model_csv(csv_path, "V_DISCENTES.csv", Discente)),
            ("NATUREZAS_FINALIDADES.csv", lambda: self.load_naturezas(csv_path)),
            ("GRUPOS_FINALIDADES.csv", lambda: self.load_grupos(csv_path)),
            ("FINALIDADES.csv", lambda: self.load_finalidades(csv_path)),
            ("TIPOS_DOCUMENTOS.csv", lambda: self.load_document_types(csv_path)),
            ("TIPOS_DOCUMENTOS_PARA_FINALIDADES.csv", lambda: self.load_document_links(csv_path)),
        ]
        with tqdm(total=len(loaders), desc="Carregando dados iniciais") as progress:
            for label, load in loaders:
                progress.set_description(f"Carregando {label}")
                count = load()
                self.stdout.write(f"{label}: {count} registros.")
                progress.update(1)

        for codigo, _ in TipoMovimento.Codigo.choices:
            TipoMovimento.obter(codigo)

        units, parents = self.load_units_counts(csv_path)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed concluído: {units} unidades, {parents} com unidade pai; "
                "catálogos legados convertidos."
            )
        )

    def load_units_counts(self, csv_path):
        rows = self.read_csv(csv_path / "UNIDADES.csv")
        parent_ids = mapear_unidade_pai(rows)
        return len(rows), sum(parent_id is not None for parent_id in parent_ids.values())
