from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from despesas.models import Finalidade, Natureza, TipoMovimento
from entidades.models import Unidade
from ngo_ccsh.management.commands.seed_dev_database import mapear_unidade_pai


class UnitHierarchyMappingTests(TestCase):
    def test_finds_nearest_same_center_parent_preserving_segment_widths(self):
        rows = [
            {"ID_UNIDADE_INTERNA": "1", "ID_CENTRO_INTERNO": "10", "COD_ESTRUTURADO": "01.00.00.00.0.0"},
            {"ID_UNIDADE_INTERNA": "2", "ID_CENTRO_INTERNO": "10", "COD_ESTRUTURADO": "01.31.00.00.0.0"},
            {"ID_UNIDADE_INTERNA": "3", "ID_CENTRO_INTERNO": "10", "COD_ESTRUTURADO": "01.31.00.01.0.0"},
            {"ID_UNIDADE_INTERNA": "4", "ID_CENTRO_INTERNO": "20", "COD_ESTRUTURADO": "02.31.00.00.0.0"},
            {"ID_UNIDADE_INTERNA": "5", "ID_CENTRO_INTERNO": "21", "COD_ESTRUTURADO": "02.31.00.01.0.0"},
        ]

        self.assertEqual(
            mapear_unidade_pai(rows),
            {1: None, 2: 1, 3: 2, 4: None, 5: None},
        )

    def test_rejects_duplicate_or_malformed_structured_codes(self):
        row = {
            "ID_UNIDADE_INTERNA": "1",
            "ID_CENTRO_INTERNO": "10",
            "COD_ESTRUTURADO": "1.31.00.00.0.0",
        }
        with self.assertRaises(ValueError):
            mapear_unidade_pai([row])
        with self.assertRaises(ValueError):
            mapear_unidade_pai([row, {**row, "ID_UNIDADE_INTERNA": "2"}])


class LegacyDatabaseSeedTests(TestCase):
    def test_converts_catalogs_and_loads_unit_hierarchy(self):
        call_command("seed_dev_database", stdout=StringIO())

        self.assertEqual(Unidade.objects.count(), 2544)
        self.assertEqual(
            Unidade.objects.filter(unidade_pai__isnull=False).count(), 2519
        )
        self.assertTrue(Natureza.objects.exists())
        self.assertTrue(Finalidade.objects.exists())
        self.assertEqual(TipoMovimento.objects.count(), 10)
        self.assertFalse(
            Finalidade.objects.filter(pk__in=[36, 37, 39, 40, 41, 42, 43, 44]).exists()
        )
