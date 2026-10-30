"""
Operações que escrevem no razão (e nas bolsas).

Regras gerais
-------------
* Toda operação roda dentro de ``transaction.atomic()`` e trava a linha do ``Centro``
  (``select_for_update``) para que duas pessoas não debitem o mesmo saldo ao mesmo
  tempo. Falhou uma invariante -> nada é gravado.
* Erros de regra de negócio levantam ``RegraDeNegocio`` (e subclasses); dados mal
  formados levantam ``django.core.exceptions.ValidationError``.
* O razão nunca é editado: corrigir é estornar e relançar (``corrigir_transacao``).
* Um exercício (centro + ano fiscal) fechado não aceita nenhum lançamento.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Sequence

from django.core.exceptions import ValidationError
from django.db import transaction
from entidades.models import Centro, Pessoa, Unidade

from . import saldos
from .models import (
    ExercicioCentro,
    Empenho,
    Finalidade,
    ItemListaSIAFI,
    Lancamento,
    ListaSIAFI,
    Natureza,
    ParcelaBolsa,
    TipoDocumento,
    TipoMovimento,
    Transacao,
    ValorDocumento,
    VinculoBolsa,
    ZERO,
)

Codigo = TipoMovimento.Codigo
Operacao = Transacao.Operacao

TRANSPORTAR = "transportar"
DEVOLVER = "devolver"

_MANTER = object()  # "não mexa" em parâmetros que também aceitam None


# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------


class RegraDeNegocio(Exception):
    """Violação de uma regra de negócio."""


class ExercicioFechado(RegraDeNegocio):
    """O ano fiscal do centro está fechado."""


class SaldoInsuficiente(RegraDeNegocio):
    """A operação deixaria algum saldo negativo."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _dinheiro(valor) -> Decimal:
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _positivo(valor, nome="montante") -> Decimal:
    valor = _dinheiro(valor)
    if valor <= 0:
        raise ValidationError(f"O {nome} precisa ser maior que zero.")
    return valor


def _travar_centros(ids: Iterable[int]) -> None:
    """Serializa as operações por centro (ordem fixa para evitar deadlock)."""
    ids = sorted(set(ids))
    if ids:
        list(Centro._base_manager.select_for_update().filter(pk__in=ids).order_by("pk"))


def _exigir_exercicio_aberto(centro_id: int, ano_fiscal: int) -> None:
    exercicio, _ = ExercicioCentro.objects.get_or_create(
        centro_id=centro_id, ano_fiscal=ano_fiscal
    )
    if exercicio.status == ExercicioCentro.Status.FECHADO:
        raise ExercicioFechado(
            f"O ano fiscal {ano_fiscal} está fechado para este centro. Para corrigir, "
            "um administrador precisa reabrir o exercício."
        )


@dataclass(frozen=True)
class LinhaSpec:
    """Descrição de uma linha do razão a ser criada."""

    tipo: str
    centro: Centro
    ano_fiscal: int
    natureza: Natureza
    montante: Decimal
    empenho: Empenho | None = None
    unidade: Unidade | None = None
    finalidade: Finalidade | None = None

    def com(self, **mudancas) -> "LinhaSpec":
        """Cópia com campos alterados (ex.: ``spec.com(montante=Decimal('-150'))``)."""
        return replace(self, **mudancas)

    @classmethod
    def de_lancamento(cls, lancamento: Lancamento, **mudancas) -> "LinhaSpec":
        return cls(
            tipo=lancamento.tipo_movimento.codigo,
            centro=lancamento.centro,
            ano_fiscal=lancamento.ano_fiscal,
            natureza=lancamento.natureza,
            montante=lancamento.montante,
            empenho=lancamento.empenho,
            unidade=lancamento.unidade,
            finalidade=lancamento.finalidade,
        ).com(**mudancas)


def linhas_vigentes(transacao: Transacao) -> list[LinhaSpec]:
    """As linhas que a transação 'afirma' (sem os estornos), como ``LinhaSpec``."""
    lancamentos = transacao.lancamentos_vigentes().select_related(
        "tipo_movimento", "centro", "natureza", "empenho", "unidade", "finalidade"
    )
    return [LinhaSpec.de_lancamento(l) for l in lancamentos.order_by("pk")]


def transacao_vigente(transacao: Transacao) -> Transacao:
    """Segue a cadeia de correções até a transação mais recente."""
    atual = transacao
    while True:
        seguinte = atual.correcoes.order_by("pk").first()
        if seguinte is None:
            return atual
        atual = seguinte


# ---------------------------------------------------------------------------
# Documentos (campos descritivos por finalidade)
# ---------------------------------------------------------------------------


def _validar_documentos(finalidade, documentos, exigir_obrigatorios):
    """
    Valida ``documentos`` (pares ``(TipoDocumento, valor)``) contra a finalidade e
    devolve ``[(tipo, valor_normalizado, ordem)]``.
    """
    documentos = list(documentos or [])
    if finalidade is None:
        if documentos:
            raise ValidationError(
                "Esta operação não tem finalidade, então não aceita documentos."
            )
        return []

    ligacoes = {
        l.tipo_documento_id: l
        for l in finalidade.tipodocumentoparafinalidade_set.filter(
            ativo=True, tipo_documento__ativo=True
        )
    }
    ordem = defaultdict(int)
    normalizados = []
    for tipo, valor in documentos:
        if tipo.pk not in ligacoes:
            raise ValidationError(
                f"O campo '{tipo.nome}' não é aceito na finalidade '{finalidade.nome}'."
            )
        normalizados.append((tipo, tipo.validar_valor(valor), ordem[tipo.pk]))
        ordem[tipo.pk] += 1

    if exigir_obrigatorios:
        faltando = [
            l.tipo_documento.nome
            for l in ligacoes.values()
            if l.obrigatorio and l.tipo_documento_id not in ordem
        ]
        if faltando:
            raise ValidationError(
                "Faltam campos obrigatórios para a finalidade "
                f"'{finalidade.nome}': {', '.join(sorted(faltando))}."
            )
    return normalizados


def _finalidade_unica(linhas: Sequence[LinhaSpec]):
    finalidades = {l.finalidade.pk: l.finalidade for l in linhas if l.finalidade}
    if len(finalidades) > 1:
        raise ValidationError(
            "Uma despesa comum só pode ter uma finalidade (para a Lista SIAFI, use "
            "pagar_lista)."
        )
    return next(iter(finalidades.values()), None)


# ---------------------------------------------------------------------------
# Núcleo: gravar uma transação com suas linhas
# ---------------------------------------------------------------------------


def _verificar_invariantes(lancamentos: Sequence[Lancamento]) -> None:
    """Confere os saldos tocados pelas linhas recém gravadas (dentro da transação)."""
    chaves = {(l.centro_id, l.ano_fiscal, l.natureza_id) for l in lancamentos}
    for centro_id, ano, natureza_id in chaves:
        total = saldos.total_centro(centro_id, ano, natureza_id)
        contexto = f"(centro {centro_id}, ano {ano}, natureza {natureza_id})"
        if total < 0:
            raise SaldoInsuficiente(f"O centro ficaria com recurso negativo {contexto}.")
        if saldos.empenhado_centro(centro_id, ano, natureza_id) > total:
            raise SaldoInsuficiente(
                f"Não há recurso livre suficiente para empenhar {contexto}."
            )
        if saldos.distribuido_centro(centro_id, ano, natureza_id) > total:
            raise SaldoInsuficiente(
                f"O centro não tem recurso suficiente para distribuir {contexto}."
            )

    for empenho in {l.empenho for l in lancamentos if l.empenho_id}:
        if saldos.saldo_empenho(empenho) < 0:
            raise SaldoInsuficiente(f"O empenho {empenho} ficaria com saldo negativo.")

    unidades = {
        (l.unidade, l.ano_fiscal, l.natureza) for l in lancamentos if l.unidade_id
    }
    for unidade, ano, natureza in unidades:
        if saldos.saldo_unidade(unidade, ano, natureza) < 0:
            raise SaldoInsuficiente(
                f"A unidade '{unidade}' ficaria com saldo negativo em {ano} "
                f"({natureza})."
            )
        if saldos.disponivel_unidade(unidade, ano, natureza) < 0:
            raise SaldoInsuficiente(
                f"A unidade '{unidade}' não tem saldo disponível em {ano} "
                f"({natureza}): o restante está alocado para bolsas."
            )


@transaction.atomic
def _gravar(
    *,
    operacao: str,
    usuario,
    linhas: Sequence[LinhaSpec],
    data: dt.date | None = None,
    justificativa: str = "",
    estimada: bool = False,
    beneficiario: Pessoa | None = None,
    corrige: Transacao | None = None,
    estornos: Sequence[Lancamento] = (),
    documentos: Sequence[tuple[TipoDocumento, str, int]] = (),
    ignorar_exercicio: frozenset = frozenset(),
) -> Transacao:
    centros = {l.centro.pk for l in linhas} | {e.centro_id for e in estornos}
    _travar_centros(centros)

    transacao = Transacao.objects.create(
        operacao=operacao,
        data=data or dt.date.today(),
        usuario=usuario,
        justificativa=justificativa,
        corrige=corrige,
        estimada=estimada,
        beneficiario=beneficiario,
    )

    novos: list[Lancamento] = []
    for original in estornos:
        novos.append(
            Lancamento(
                transacao=transacao,
                tipo_movimento_id=original.tipo_movimento_id,
                centro_id=original.centro_id,
                ano_fiscal=original.ano_fiscal,
                natureza_id=original.natureza_id,
                empenho_id=original.empenho_id,
                unidade_id=original.unidade_id,
                finalidade_id=original.finalidade_id,
                montante=-original.montante,
                estorna=original,
            )
        )
    for spec in linhas:
        novos.append(
            Lancamento(
                transacao=transacao,
                tipo_movimento=TipoMovimento.obter(spec.tipo),
                centro=spec.centro,
                ano_fiscal=spec.ano_fiscal,
                natureza=spec.natureza,
                empenho=spec.empenho,
                unidade=spec.unidade,
                finalidade=spec.finalidade,
                montante=_dinheiro(spec.montante),
            )
        )

    for chave in {(l.centro_id, l.ano_fiscal) for l in novos}:
        if chave not in ignorar_exercicio:
            _exigir_exercicio_aberto(*chave)

    for lancamento in novos:
        lancamento.save()
    _verificar_invariantes(novos)

    for tipo, valor, ordem in documentos:
        ValorDocumento.objects.create(
            transacao=transacao, tipo_documento=tipo, ordem=ordem, valor=valor
        )
    return transacao


# ---------------------------------------------------------------------------
# Créditos, empenhos e distribuição
# ---------------------------------------------------------------------------


def creditar(
    centro: Centro,
    ano_fiscal: int,
    natureza: Natureza,
    montante,
    usuario,
    *,
    extraordinario: bool = False,
    data=None,
    justificativa: str = "",
) -> Transacao:
    """Recurso recebido da PROPLAN (ordinário ou extraordinário)."""
    tipo = Codigo.CREDITO_EXTRAORDINARIO if extraordinario else Codigo.CREDITO_ORDINARIO
    linha = LinhaSpec(tipo, centro, ano_fiscal, natureza, _positivo(montante))
    return _gravar(
        operacao=Operacao.CREDITO,
        usuario=usuario,
        linhas=[linha],
        data=data,
        justificativa=justificativa,
    )


def reforcar_empenho(
    empenho: Empenho, montante, usuario, *, data=None, justificativa: str = ""
) -> Transacao:
    """
    Empenha (reserva) mais recurso livre do centro. Atenção: no SIAFI isso é um
    compromisso irreversível; aqui, para desfazer, só corrigindo a transação.
    """
    linha = LinhaSpec(
        Codigo.REFORCO_EMPENHO,
        empenho.centro,
        empenho.ano_fiscal,
        empenho.natureza,
        _positivo(montante),
        empenho=empenho,
    )
    return _gravar(
        operacao=Operacao.REFORCO,
        usuario=usuario,
        linhas=[linha],
        data=data,
        justificativa=justificativa,
    )


def distribuir(
    centro: Centro,
    ano_fiscal: int,
    natureza: Natureza,
    unidade: Unidade,
    montante,
    usuario,
    *,
    data=None,
    justificativa: str = "",
) -> Transacao:
    """O centro entrega um 'cheque' à subunidade (sai do recurso não distribuído)."""
    linha = LinhaSpec(
        Codigo.DISTRIBUICAO,
        centro,
        ano_fiscal,
        natureza,
        _positivo(montante),
        unidade=unidade,
    )
    return _gravar(
        operacao=Operacao.DISTRIBUICAO,
        usuario=usuario,
        linhas=[linha],
        data=data,
        justificativa=justificativa,
    )


def recolher_de_unidade(
    centro: Centro,
    ano_fiscal: int,
    natureza: Natureza,
    unidade: Unidade,
    montante,
    usuario,
    *,
    data=None,
    justificativa: str = "",
) -> Transacao:
    """Devolve ao centro parte do 'cheque' de uma subunidade (só o que está disponível)."""
    linha = LinhaSpec(
        Codigo.DISTRIBUICAO,
        centro,
        ano_fiscal,
        natureza,
        -_positivo(montante),
        unidade=unidade,
    )
    return _gravar(
        operacao=Operacao.DISTRIBUICAO,
        usuario=usuario,
        linhas=[linha],
        data=data,
        justificativa=justificativa,
    )


def transferir_entre_unidades(
    centro: Centro,
    ano_fiscal: int,
    natureza: Natureza,
    origem: Unidade,
    destino: Unidade,
    montante,
    usuario,
    *,
    data=None,
    justificativa: str = "",
) -> Transacao:
    valor = _positivo(montante)
    linhas = [
        LinhaSpec(Codigo.DISTRIBUICAO, centro, ano_fiscal, natureza, -valor, unidade=origem),
        LinhaSpec(Codigo.DISTRIBUICAO, centro, ano_fiscal, natureza, valor, unidade=destino),
    ]
    return _gravar(
        operacao=Operacao.DISTRIBUICAO,
        usuario=usuario,
        linhas=linhas,
        data=data,
        justificativa=justificativa,
    )


# ---------------------------------------------------------------------------
# Despesas
# ---------------------------------------------------------------------------


def registrar_despesa(
    empenho: Empenho,
    unidade: Unidade | None,
    finalidade: Finalidade,
    montante,
    usuario,
    *,
    beneficiario: Pessoa | None = None,
    documentos: Sequence[tuple[TipoDocumento, str]] = (),
    estimada: bool = False,
    administrativo: bool = False,
    data=None,
    justificativa: str = "",
) -> Transacao:
    """
    Registra uma despesa: debita o empenho e (se informada) a unidade, na mesma linha.
    ``unidade=None`` significa que o centro paga com recurso próprio (não distribuído).

    ``estimada=True`` registra já o compromisso mesmo sem todos os documentos
    obrigatórios (diárias antes das notas fiscais, por exemplo); a correção posterior
    troca o valor e marca como definitiva.

    ``administrativo=True`` é o centro debitando o saldo de uma subunidade que não o
    usou (ex.: obra emergencial); exige unidade e justificativa.
    """
    if administrativo:
        if unidade is None:
            raise ValidationError("Um débito administrativo precisa de uma unidade.")
        if not justificativa.strip():
            raise ValidationError("Um débito administrativo exige justificativa.")
        tipo, operacao = Codigo.DEBITO_ADMINISTRATIVO, Operacao.DEBITO_ADMINISTRATIVO
    else:
        tipo, operacao = Codigo.PAGAMENTO, Operacao.DESPESA

    linha = LinhaSpec(
        tipo,
        empenho.centro,
        empenho.ano_fiscal,
        empenho.natureza,
        -_positivo(montante),
        empenho=empenho,
        unidade=unidade,
        finalidade=finalidade,
    )
    docs = _validar_documentos(finalidade, documentos, exigir_obrigatorios=not estimada)
    return _gravar(
        operacao=operacao,
        usuario=usuario,
        linhas=[linha],
        data=data,
        justificativa=justificativa,
        estimada=estimada,
        beneficiario=beneficiario,
        documentos=docs,
    )


def converter_natureza(
    empenho_origem: Empenho,
    empenho_destino: Empenho,
    montante,
    usuario,
    *,
    unidade: Unidade | None = None,
    data=None,
    justificativa: str = "",
) -> Transacao:
    """
    Converte recurso de uma natureza para outra (regra 6): tira do empenho de origem e
    coloca no de destino (que tem outra natureza), e move junto o saldo da unidade.
    """
    if empenho_origem.centro_id != empenho_destino.centro_id:
        raise ValidationError("Os empenhos precisam ser do mesmo centro.")
    if empenho_origem.ano_fiscal != empenho_destino.ano_fiscal:
        raise ValidationError("Os empenhos precisam ser do mesmo ano fiscal.")
    if empenho_origem.natureza_id == empenho_destino.natureza_id:
        raise ValidationError("A conversão exige empenhos de naturezas diferentes.")
    valor = _positivo(montante)
    linhas = [
        LinhaSpec(
            Codigo.CONVERSAO_NATUREZA,
            empenho_origem.centro,
            empenho_origem.ano_fiscal,
            empenho_origem.natureza,
            -valor,
            empenho=empenho_origem,
            unidade=unidade,
        ),
        LinhaSpec(
            Codigo.CONVERSAO_NATUREZA,
            empenho_destino.centro,
            empenho_destino.ano_fiscal,
            empenho_destino.natureza,
            valor,
            empenho=empenho_destino,
            unidade=unidade,
        ),
    ]
    return _gravar(
        operacao=Operacao.CONVERSAO,
        usuario=usuario,
        linhas=linhas,
        data=data,
        justificativa=justificativa,
    )


# ---------------------------------------------------------------------------
# Correções
# ---------------------------------------------------------------------------

_NAO_CORRIGIVEIS = {Operacao.FECHAMENTO, Operacao.REABERTURA, Operacao.LISTA_SIAFI}


@transaction.atomic
def corrigir_transacao(
    transacao: Transacao,
    usuario,
    *,
    justificativa: str = "",
    linhas: Sequence[LinhaSpec] | None = None,
    documentos: Sequence[tuple[TipoDocumento, str]] | None = None,
    estimada: bool | None = None,
    beneficiario=_MANTER,
    data: dt.date | None = None,
) -> Transacao:
    """
    "Edita" uma transação: estorna as linhas vigentes e grava as novas, tudo em uma
    nova ``Transacao`` ligada à original por ``corrige``.

    * ``linhas=None`` mantém as linhas como estão (útil para só trocar documentos,
      data ou o flag ``estimada``); para mudar valores, parta de
      ``linhas_vigentes(transacao)`` e use ``spec.com(montante=...)``.
    * ``documentos=None`` copia os documentos da transação original.
    * Corrigir uma transação definitiva exige ``justificativa``; corrigir uma
      estimada (o caso das diárias) não.
    * Exercício fechado bloqueia a correção (reabra o exercício antes).
    * Pagamentos de Lista SIAFI, fechamentos e reaberturas não são corrigidos por
      aqui.
    """
    if transacao.operacao in _NAO_CORRIGIVEIS:
        raise RegraDeNegocio(
            f"Transações do tipo '{transacao.get_operacao_display()}' não são "
            "corrigidas por esta operação."
        )
    if transacao.correcoes.exists():
        raise RegraDeNegocio(
            "Esta transação já foi corrigida; corrija a transação mais recente "
            "(veja transacao_vigente)."
        )
    if not transacao.estimada and not justificativa.strip():
        raise ValidationError("Corrigir uma transação definitiva exige justificativa.")

    vigentes = list(
        transacao.lancamentos_vigentes().select_related(
            "tipo_movimento", "centro", "natureza", "empenho", "unidade", "finalidade"
        )
    )
    novas = list(linhas) if linhas is not None else [
        LinhaSpec.de_lancamento(l) for l in vigentes
    ]
    estimada_final = transacao.estimada if estimada is None else estimada
    beneficiario_final = (
        transacao.beneficiario if beneficiario is _MANTER else beneficiario
    )

    if documentos is None:
        documentos = [
            (v.tipo_documento, v.valor) for v in transacao.documentos.select_related("tipo_documento")
        ]
    docs = _validar_documentos(
        _finalidade_unica(novas), documentos, exigir_obrigatorios=not estimada_final
    )

    return _gravar(
        operacao=Operacao.CORRECAO,
        usuario=usuario,
        linhas=novas,
        data=data or transacao.data,
        justificativa=justificativa,
        estimada=estimada_final,
        beneficiario=beneficiario_final,
        corrige=transacao,
        estornos=vigentes,
        documentos=docs,
    )


# ---------------------------------------------------------------------------
# Fechamento e reabertura do exercício
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DestinoSaldo:
    """
    Destino de uma parte do saldo no fechamento.

    ``acao`` é ``TRANSPORTAR`` (vai para ``novo_empenho``, do ano seguinte) ou
    ``DEVOLVER`` (volta à PROPLAN, o que conta como gasto). Informe de qual
    ``unidade`` sai a parte (o debito do 'cheque'); ``unidade=None`` debita o recurso
    do centro que não foi distribuído. ``empenho=None`` trata recurso não empenhado
    (nesse caso informe a ``natureza``).
    """

    acao: str
    montante: Decimal
    empenho: Empenho | None = None
    unidade: Unidade | None = None
    novo_empenho: Empenho | None = None
    natureza: Natureza | None = None


@transaction.atomic
def fechar_exercicio(
    centro: Centro, ano_fiscal: int, usuario, destinos: Sequence[DestinoSaldo], *, data=None
) -> Transacao:
    """
    Fecha o ano fiscal de um centro. Cada empenho com saldo precisa de um destino
    (transportar ou devolver), e cada unidade com saldo precisa ser debitada (quem
    decide de qual unidade sai cada parte é a pessoa do centro, via ``destinos``).
    No fim tudo precisa estar zerado, senão nada é gravado.
    """
    _travar_centros([centro.pk])
    exercicio, _ = ExercicioCentro.objects.get_or_create(
        centro=centro, ano_fiscal=ano_fiscal
    )
    if exercicio.status == ExercicioCentro.Status.FECHADO:
        raise ExercicioFechado(f"O ano fiscal {ano_fiscal} já está fechado.")

    alocadas = ParcelaBolsa.objects.filter(
        status=ParcelaBolsa.Status.ALOCADA,
        ano_fiscal=ano_fiscal,
        vinculo__unidade__centro=centro,
    ).count()
    if alocadas:
        raise RegraDeNegocio(
            f"Existem {alocadas} parcelas de bolsa alocadas e não pagas em {ano_fiscal}. "
            "Pague (Lista SIAFI) ou cancele antes de fechar."
        )

    linhas: list[LinhaSpec] = []
    entradas: dict[int, list] = {}
    for destino in destinos:
        valor = _positivo(destino.montante)
        natureza = destino.natureza or (
            destino.empenho.natureza if destino.empenho else None
        )
        if natureza is None:
            raise ValidationError("Informe a natureza quando não há empenho.")
        if destino.empenho and (
            destino.empenho.centro_id != centro.pk
            or destino.empenho.ano_fiscal != ano_fiscal
        ):
            raise ValidationError("O empenho não é deste centro/ano fiscal.")
        if destino.unidade and destino.unidade.centro_id != centro.pk:
            raise ValidationError("A unidade não é deste centro.")

        if destino.acao == DEVOLVER:
            linhas.append(
                LinhaSpec(
                    Codigo.DEVOLUCAO_PROPLAN,
                    centro,
                    ano_fiscal,
                    natureza,
                    -valor,
                    empenho=destino.empenho,
                    unidade=destino.unidade,
                )
            )
        elif destino.acao == TRANSPORTAR:
            novo = destino.novo_empenho
            if destino.empenho is None or novo is None:
                raise ValidationError(
                    "Transportar exige o empenho de origem e o novo empenho."
                )
            if novo.empenho_origem_id != destino.empenho.pk:
                raise ValidationError(
                    f"O empenho {novo} não declara {destino.empenho} como origem."
                )
            if novo.ano_fiscal != ano_fiscal + 1:
                raise ValidationError("O novo empenho precisa ser do ano seguinte.")
            if not destino.empenho.finalidade.permite_transporte:
                raise RegraDeNegocio(
                    f"A finalidade '{destino.empenho.finalidade}' não permite "
                    "transportar saldo: o valor deve ser devolvido à PROPLAN."
                )
            linhas.append(
                LinhaSpec(
                    Codigo.TRANSPORTE_SAIDA,
                    centro,
                    ano_fiscal,
                    natureza,
                    -valor,
                    empenho=destino.empenho,
                    unidade=destino.unidade,
                )
            )
            acumulado = entradas.setdefault(novo.pk, [novo, ZERO])
            acumulado[1] += valor
        else:
            raise ValidationError(f"Ação desconhecida: {destino.acao!r}.")

    for novo, valor in entradas.values():
        linhas.append(
            LinhaSpec(
                Codigo.TRANSPORTE_ENTRADA,
                centro,
                ano_fiscal + 1,
                novo.natureza,
                valor,
                empenho=novo,
            )
        )

    transacao = _gravar(
        operacao=Operacao.FECHAMENTO,
        usuario=usuario,
        linhas=linhas,
        data=data,
        justificativa=f"Fechamento do exercício {ano_fiscal}",
    )

    pendencias = saldos.pendencias_fechamento(centro, ano_fiscal)
    if not pendencias["ok"]:
        raise RegraDeNegocio(
            "O fechamento deixaria saldos abertos: "
            f"{len(pendencias['empenhos'])} empenho(s), "
            f"{len(pendencias['unidades'])} saldo(s) de unidade, "
            f"total do centro {pendencias['totais']}. "
            "Use saldos.pendencias_fechamento para detalhar."
        )

    exercicio.status = ExercicioCentro.Status.FECHADO
    exercicio.transacao_fechamento = transacao
    exercicio.save()
    return transacao


@transaction.atomic
def reabrir_exercicio(
    centro: Centro, ano_fiscal: int, usuario, justificativa: str, *, data=None
) -> Transacao:
    """
    Reabre um exercício fechado, estornando as linhas do fechamento. Falha (sem
    gravar nada) se, por exemplo, o saldo transportado já tiver sido gasto no ano
    seguinte: nesse caso, resolva o ano seguinte primeiro.
    """
    if not justificativa.strip():
        raise ValidationError("Reabrir um exercício exige justificativa.")
    _travar_centros([centro.pk])
    exercicio = (
        ExercicioCentro.objects.select_for_update()
        .filter(centro=centro, ano_fiscal=ano_fiscal)
        .first()
    )
    if exercicio is None or exercicio.status != ExercicioCentro.Status.FECHADO:
        raise RegraDeNegocio("O exercício não está fechado.")

    fechamento = exercicio.transacao_fechamento
    estornos = list(
        fechamento.lancamentos_vigentes().select_related("tipo_movimento")
    )
    transacao = _gravar(
        operacao=Operacao.REABERTURA,
        usuario=usuario,
        linhas=[],
        data=data,
        justificativa=justificativa,
        estornos=estornos,
        ignorar_exercicio=frozenset({(centro.pk, ano_fiscal)}),
    )
    exercicio.status = ExercicioCentro.Status.ABERTO
    exercicio.transacao_fechamento = None
    exercicio.save()
    return transacao


# ---------------------------------------------------------------------------
# Bolsas: parcelas, alocação e Lista SIAFI
# ---------------------------------------------------------------------------


def gerar_parcelas(vinculo: VinculoBolsa) -> list[ParcelaBolsa]:
    """
    Cria as parcelas mensais (status PREVISTA) de um vínculo, do mês de início ao mês
    de fim, inclusive. Meses que já têm parcela são ignorados. O valor é o mensal
    cheio (sem proporcional de meio de mês).
    """
    existentes = set(vinculo.parcelas.values_list("competencia", flat=True))
    competencia = vinculo.inicio.replace(day=1)
    ultimo = vinculo.fim.replace(day=1)
    criadas = []
    while competencia <= ultimo:
        if competencia not in existentes:
            criadas.append(
                ParcelaBolsa.objects.create(
                    vinculo=vinculo, competencia=competencia, valor=vinculo.valor_mensal
                )
            )
        competencia = (competencia + dt.timedelta(days=32)).replace(day=1)
    return criadas


@transaction.atomic
def alocar_parcela(parcela: ParcelaBolsa, empenho_previsto: Empenho | None = None) -> ParcelaBolsa:
    """
    Reserva o valor da parcela no saldo da subunidade (plano, fora do razão). Só
    funciona se a subunidade tiver saldo *disponível* naquele ano e natureza; caso
    contrário a parcela continua PREVISTA (aparece no compromisso futuro).
    ``empenho_previsto`` indica qual empenho deve pagá-la (base do alerta de
    complemento do empenho).
    """
    unidade = parcela.vinculo.unidade
    natureza = parcela.vinculo.finalidade.natureza
    _travar_centros([unidade.centro_id])
    parcela.refresh_from_db()

    if parcela.status != ParcelaBolsa.Status.PREVISTA:
        raise RegraDeNegocio(f"A parcela está {parcela.get_status_display().lower()}.")
    _exigir_exercicio_aberto(unidade.centro_id, parcela.ano_fiscal)

    if empenho_previsto is not None:
        if (
            empenho_previsto.centro_id != unidade.centro_id
            or empenho_previsto.ano_fiscal != parcela.ano_fiscal
            or empenho_previsto.natureza_id != natureza.pk
        ):
            raise ValidationError(
                "O empenho previsto precisa ser do mesmo centro, ano fiscal e natureza."
            )

    disponivel = saldos.disponivel_unidade(unidade, parcela.ano_fiscal, natureza)
    if disponivel < parcela.valor:
        raise SaldoInsuficiente(
            f"A unidade '{unidade}' tem {disponivel} disponível em {parcela.ano_fiscal} "
            f"({natureza}) e a parcela é de {parcela.valor}: ela permanece prevista."
        )

    parcela.status = ParcelaBolsa.Status.ALOCADA
    parcela.empenho_previsto = empenho_previsto
    parcela.save()
    return parcela


@transaction.atomic
def cancelar_parcela(parcela: ParcelaBolsa) -> ParcelaBolsa:
    """Cancela a parcela (bolsa cancelada, por exemplo), liberando a reserva."""
    _travar_centros([parcela.vinculo.unidade.centro_id])
    parcela.refresh_from_db()
    if parcela.status == ParcelaBolsa.Status.PAGA:
        raise RegraDeNegocio("Parcela já paga: corrija o pagamento, não cancele.")
    ItemListaSIAFI.objects.filter(
        parcela=parcela, lista__status=ListaSIAFI.Status.RASCUNHO
    ).delete()
    parcela.status = ParcelaBolsa.Status.CANCELADA
    parcela.save()
    return parcela


def criar_lista(centro: Centro, competencia: dt.date) -> ListaSIAFI:
    return ListaSIAFI.objects.create(centro=centro, competencia=competencia)


@transaction.atomic
def incluir_parcelas(lista: ListaSIAFI, parcelas: Iterable[ParcelaBolsa]) -> list[ItemListaSIAFI]:
    """Coloca parcelas ALOCADAS da competência da lista em uma Lista SIAFI (rascunho)."""
    lista.refresh_from_db()
    if lista.status != ListaSIAFI.Status.RASCUNHO:
        raise RegraDeNegocio("A lista já foi paga.")
    itens = []
    for parcela in parcelas:
        parcela.refresh_from_db()
        if parcela.status != ParcelaBolsa.Status.ALOCADA:
            raise RegraDeNegocio(
                f"A parcela {parcela} precisa estar alocada para entrar em uma lista."
            )
        if parcela.competencia != lista.competencia:
            raise ValidationError("A parcela é de outra competência.")
        if parcela.vinculo.unidade.centro_id != lista.centro_id:
            raise ValidationError("A parcela é de uma unidade de outro centro.")
        if hasattr(parcela, "item_lista"):
            raise RegraDeNegocio("A parcela já está em uma lista.")
        itens.append(
            ItemListaSIAFI.objects.create(lista=lista, parcela=parcela, valor=parcela.valor)
        )
    return itens


@transaction.atomic
def pagar_lista(
    lista: ListaSIAFI,
    usuario,
    numero_siafi: str,
    *,
    divisoes: dict[int, Sequence[tuple[Empenho, Decimal]]] | None = None,
    data=None,
) -> Transacao:
    """
    Registra a Lista SIAFI como paga (o pagamento de fato aconteceu em outro sistema) e
    gera todos os lançamentos de uma vez.

    Por padrão cada item sai do ``empenho_previsto`` da sua parcela. Para completar
    com outro empenho (fim de ano), passe ``divisoes={item.pk: [(empenho, valor), ...]}``;
    a soma das partes precisa ser igual ao valor do item. ``numero_siafi`` é a chave
    de conciliação com o outro sistema e é obrigatório.
    """
    numero = (numero_siafi or "").strip()
    if not numero:
        raise ValidationError("Informe o número da Lista no SIAFI para confirmar.")
    _travar_centros([lista.centro_id])
    lista = ListaSIAFI.objects.get(pk=lista.pk)
    if lista.status != ListaSIAFI.Status.RASCUNHO:
        raise RegraDeNegocio("A lista já foi paga.")

    itens = list(
        lista.itens.select_related(
            "parcela__vinculo__unidade",
            "parcela__vinculo__finalidade__natureza",
            "parcela__empenho_previsto",
        )
    )
    if not itens:
        raise RegraDeNegocio("A lista está vazia.")

    divisoes = divisoes or {}
    linhas: list[LinhaSpec] = []
    for item in itens:
        parcela = item.parcela
        if parcela.status != ParcelaBolsa.Status.ALOCADA:
            raise RegraDeNegocio(f"A parcela {parcela} não está alocada.")
        partes = divisoes.get(item.pk)
        if partes is None:
            if parcela.empenho_previsto is None:
                raise RegraDeNegocio(
                    f"Informe de qual empenho sai a parcela de {parcela.vinculo.bolsista}."
                )
            partes = [(parcela.empenho_previsto, item.valor)]
        if sum((_dinheiro(v) for _, v in partes), ZERO) != item.valor:
            raise ValidationError(
                f"As partes da parcela de {parcela.vinculo.bolsista} não somam {item.valor}."
            )
        for empenho, valor in partes:
            if empenho.centro_id != lista.centro_id or empenho.ano_fiscal != lista.ano_fiscal:
                raise ValidationError(
                    f"O empenho {empenho} não é do centro/ano fiscal desta lista."
                )
            linhas.append(
                LinhaSpec(
                    Codigo.PAGAMENTO,
                    lista.centro,
                    lista.ano_fiscal,
                    empenho.natureza,
                    -_positivo(valor),
                    empenho=empenho,
                    unidade=parcela.vinculo.unidade,
                    finalidade=parcela.vinculo.finalidade,
                )
            )

    # As parcelas deixam de contar como "alocadas" antes de conferir os saldos: o
    # saldo da unidade e o alocado caem juntos, então o disponível não muda.
    for item in itens:
        item.parcela.status = ParcelaBolsa.Status.PAGA
        item.parcela.save()

    transacao = _gravar(
        operacao=Operacao.LISTA_SIAFI,
        usuario=usuario,
        linhas=linhas,
        data=data,
        justificativa=f"Lista SIAFI {numero}",
    )
    lista.numero_siafi = numero
    lista.status = ListaSIAFI.Status.PAGA
    lista.transacao = transacao
    lista.save()
    return transacao
