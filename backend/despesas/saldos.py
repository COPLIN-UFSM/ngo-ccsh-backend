"""
Consultas de saldo (somente leitura).

Todo saldo é uma soma simples sobre o razão (``Lancamento``); como o razão só recebe
linhas novas (correções entram como estornos), nunca é preciso "achar a versão
vigente". As consultas de bolsas somam ``ParcelaBolsa`` (plano, fora do razão).

Termos
------
* **saldo** de empenho/unidade: soma das linhas do razão naquela dimensão;
* **alocado** de uma unidade: parcelas de bolsa ALOCADAS e ainda não pagas;
* **disponível** de uma unidade: saldo - alocado;
* **total** do centro: soma das linhas que alteram o total (créditos, pagamentos...);
* **livre** (não empenhado): total - soma das linhas com empenho;
* **do centro** (não distribuído): total - soma das linhas com unidade.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum

from .models import (
    ZERO,
    Empenho,
    Lancamento,
    ParcelaBolsa,
)


def _soma(queryset, campo="montante") -> Decimal:
    return queryset.aggregate(t=Sum(campo))["t"] or ZERO


# --- razão -----------------------------------------------------------------


def saldo_empenho(empenho) -> Decimal:
    return _soma(Lancamento.objects.filter(empenho=empenho))


def gasto_empenho(empenho) -> Decimal:
    return -_soma(
        Lancamento.objects.filter(
            empenho=empenho, tipo_movimento__conta_como_gasto=True
        )
    )


def saldo_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            unidade=unidade, ano_fiscal=ano_fiscal, natureza=natureza
        )
    )


def total_centro(centro, ano_fiscal, natureza) -> Decimal:
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            tipo_movimento__altera_total=True,
        )
    )


def empenhado_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Soma dos saldos de todos os empenhos do centro naquele ano e natureza."""
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            empenho__isnull=False,
        )
    )


def distribuido_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Soma dos saldos de todas as unidades do centro naquele ano e natureza."""
    return _soma(
        Lancamento.objects.filter(
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            unidade__isnull=False,
        )
    )


def livre_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Recurso do centro que ainda não foi empenhado."""
    return total_centro(centro, ano_fiscal, natureza) - empenhado_centro(
        centro, ano_fiscal, natureza
    )


def nao_distribuido_centro(centro, ano_fiscal, natureza) -> Decimal:
    """Recurso do centro que ainda não foi distribuído às subunidades."""
    return total_centro(centro, ano_fiscal, natureza) - distribuido_centro(
        centro, ano_fiscal, natureza
    )


# --- bolsas (plano) ---------------------------------------------------------


def alocado_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return _soma(
        ParcelaBolsa.objects.filter(
            vinculo__unidade=unidade,
            vinculo__finalidade__natureza=natureza,
            ano_fiscal=ano_fiscal,
            status=ParcelaBolsa.Status.ALOCADA,
        ),
        campo="valor",
    )


def disponivel_unidade(unidade, ano_fiscal, natureza) -> Decimal:
    return saldo_unidade(unidade, ano_fiscal, natureza) - alocado_unidade(
        unidade, ano_fiscal, natureza
    )


def previsto_empenho(empenho) -> Decimal:
    """Parcelas alocadas que devem sair deste empenho e ainda não foram pagas."""
    return _soma(
        ParcelaBolsa.objects.filter(
            empenho_previsto=empenho, status=ParcelaBolsa.Status.ALOCADA
        ),
        campo="valor",
    )


def a_complementar(empenho) -> Decimal:
    """
    Quanto falta empenhar (reforçar) para cobrir o que já está alocado para sair deste
    empenho. Zero quando o empenho já cobre tudo.
    """
    falta = previsto_empenho(empenho) - saldo_empenho(empenho)
    return falta if falta > 0 else ZERO


def compromisso_futuro(centro=None) -> dict:
    """
    Parcelas ainda PREVISTAS (sem reserva), somadas por ano fiscal. É o relatório de
    "compromisso futuro": o que já se sabe que será preciso pagar, mas ainda não tem
    orçamento distribuído para reservar.
    """
    parcelas = ParcelaBolsa.objects.filter(status=ParcelaBolsa.Status.PREVISTA)
    if centro is not None:
        parcelas = parcelas.filter(vinculo__unidade__centro=centro)
    linhas = parcelas.values("ano_fiscal").annotate(total=Sum("valor"))
    return {linha["ano_fiscal"]: linha["total"] for linha in linhas.order_by("ano_fiscal")}


# --- fechamento ---------------------------------------------------------------


def pendencias_fechamento(centro, ano_fiscal) -> dict:
    """
    O que ainda impede o fechamento do exercício: tudo precisa estar zerado.

    Retorna ``{"ok": bool, "empenhos": [(Empenho, saldo)], "unidades":
    [(unidade_id, natureza_id, saldo)], "totais": [(natureza_id, total)],
    "parcelas_alocadas": int}``.
    """
    base = Lancamento.objects.filter(centro=centro, ano_fiscal=ano_fiscal)

    por_empenho = (
        base.filter(empenho__isnull=False)
        .values("empenho")
        .annotate(s=Sum("montante"))
    )
    saldos_empenho = {l["empenho"]: l["s"] for l in por_empenho if l["s"] != 0}
    empenhos = Empenho.objects.in_bulk(list(saldos_empenho))

    por_unidade = (
        base.filter(unidade__isnull=False)
        .values("unidade", "natureza")
        .annotate(s=Sum("montante"))
    )
    unidades = [
        (l["unidade"], l["natureza"], l["s"]) for l in por_unidade if l["s"] != 0
    ]

    totais = defaultdict(lambda: ZERO)
    for l in (
        base.filter(tipo_movimento__altera_total=True)
        .values("natureza")
        .annotate(s=Sum("montante"))
    ):
        totais[l["natureza"]] += l["s"]
    totais = [(n, t) for n, t in totais.items() if t != 0]

    parcelas = ParcelaBolsa.objects.filter(
        status=ParcelaBolsa.Status.ALOCADA,
        ano_fiscal=ano_fiscal,
        vinculo__unidade__centro=centro,
    ).count()

    resultado = {
        "empenhos": [(empenhos[pk], s) for pk, s in saldos_empenho.items()],
        "unidades": unidades,
        "totais": totais,
        "parcelas_alocadas": parcelas,
    }
    resultado["ok"] = not (
        resultado["empenhos"] or unidades or totais or parcelas
    )
    return resultado
