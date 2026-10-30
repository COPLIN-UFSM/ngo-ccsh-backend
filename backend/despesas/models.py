"""
Modelos do sistema de despesas (book-keeping: o pagamento de fato é feito em outro sistema).

Ideia central
-------------
O dinheiro de um centro é um só, visto por duas "partições" independentes:

* **por empenho**: quanto está reservado em cada empenho;
* **por unidade**: quanto cada subunidade tem de "cheque".

Tudo isso mora em um único razão imutável (``Lancamento``). Cada linha tem
``empenho`` e ``unidade`` opcionais:

* ``empenho`` preenchido  -> a linha mexe na partição por empenho;
* ``unidade`` preenchida  -> a linha mexe na partição por unidade;
* ``tipo_movimento.altera_total`` -> a linha muda o total do centro (crédito,
  pagamento, devolução...). Reforço de empenho e distribuição para subunidade só
  movem dinheiro *dentro* do centro e não alteram o total.

Dois "baldes" são derivados, nunca armazenados:

* recurso livre (não empenhado)        = total - soma das linhas com empenho;
* recurso do centro (não distribuído)  = total - soma das linhas com unidade.

Invariantes (verificadas em ``services``) por (centro, ano fiscal, natureza):
total >= 0, empenhado <= total, distribuído <= total; e cada empenho e cada
unidade com saldo >= 0.

Estados do dinheiro de bolsas
-----------------------------
* **alocado** (``ParcelaBolsa.status == ALOCADA``): reserva o saldo da subunidade,
  mas é só um plano, fora do razão; pode ser cancelado;
* **empenhado**: lançamento de reforço no razão, decisão irreversível (SIAFI);
* **pago**: lançamento de pagamento no razão (nas duas dimensões).

Correções
---------
O razão só recebe linhas novas. "Editar" uma transação é criar outra transação
(``Transacao.corrige``) com o estorno das linhas vigentes e as novas linhas. Para
as demais entidades (vínculos, parcelas, listas, empenhos...), o "quem mudou o quê"
vem de ``django-simple-history`` (opcional: sem a biblioteca o código funciona,
só não há histórico).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum

from entidades.models import Discente, Servidor

try:  # django-simple-history é opcional
    from simple_history.models import HistoricalRecords
except ImportError:  # pragma: no cover
    HistoricalRecords = None

ZERO = Decimal("0.00")


def _historico():
    return HistoricalRecords() if HistoricalRecords is not None else None


class ImutavelError(Exception):
    """Tentativa de alterar ou apagar uma linha do razão."""


# ---------------------------------------------------------------------------
# Catálogo: naturezas, grupos, finalidades e documentos
# ---------------------------------------------------------------------------


class Natureza(models.Model):
    """
    A natureza determina para o quê um recurso é usado. Primordiais: Custeio e
    Capital. Derivadas: recursos recebidos de outras unidades para fins específicos
    (bolsas PROGRAD, bolsas PRAE...).
    """

    nome = models.CharField(max_length=256, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "naturezas"
        verbose_name_plural = "naturezas"

    def __str__(self) -> str:
        return self.nome


class GrupoFinalidade(models.Model):
    """
    Agrupa finalidades parecidas (Bolsas 2A, Bolsas PRAE, Monitoria -> grupo Bolsas).
    Serve só para relatório; não carrega regra.
    """

    nome = models.CharField(max_length=256, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "grupos_finalidades"

    def __str__(self) -> str:
        return self.nome


class Finalidade(models.Model):
    """
    Destino de uma despesa (bolsa 2A, obra, passagem...). Cada finalidade tem uma
    única natureza (regra 8). ``permite_transporte`` diz se o saldo de um empenho
    dessa finalidade pode passar para o ano seguinte (regras 16 e 17); se não puder,
    o que sobra é devolvido à PROPLAN.
    """

    nome = models.CharField(max_length=512, unique=True)
    natureza = models.ForeignKey(
        Natureza, on_delete=models.PROTECT, related_name="finalidades"
    )
    grupo = models.ForeignKey(
        GrupoFinalidade,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="finalidades",
    )
    permite_transporte = models.BooleanField(default=False)
    tipos_documentos = models.ManyToManyField(
        "TipoDocumento",
        through="TipoDocumentoParaFinalidade",
        related_name="finalidades",
    )
    ativo = models.BooleanField(default=True)

    history = _historico()

    class Meta:
        db_table = "finalidades"

    def __str__(self) -> str:
        return self.nome


class TipoDocumento(models.Model):
    """
    Informação (documento ou campo) exigida por algumas finalidades: nota fiscal,
    trecho (só em passagens), número de processo... Todos são descritivos.
    """

    class TipoDado(models.TextChoices):
        TEXTO = "texto", "Texto"
        DATA = "data", "Data (AAAA-MM-DD)"
        NUMERO = "numero", "Número"

    nome = models.CharField(max_length=128, unique=True)
    tipo_dado = models.CharField(
        max_length=16, choices=TipoDado.choices, default=TipoDado.TEXTO
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "tipos_documentos"

    def __str__(self) -> str:
        return self.nome

    def validar_valor(self, valor) -> str:
        """Valida e normaliza um valor de acordo com ``tipo_dado``."""
        texto = str(valor).strip()
        if not texto:
            raise ValidationError(f"O campo '{self.nome}' não pode ficar vazio.")
        if self.tipo_dado == self.TipoDado.DATA:
            try:
                date.fromisoformat(texto)
            except ValueError:
                raise ValidationError(
                    f"'{texto}' não é uma data válida para '{self.nome}' (use AAAA-MM-DD)."
                )
        elif self.tipo_dado == self.TipoDado.NUMERO:
            try:
                texto = str(Decimal(texto.replace(",", ".")))
            except InvalidOperation:
                raise ValidationError(
                    f"'{texto}' não é um número válido para '{self.nome}'."
                )
        return texto


class TipoDocumentoParaFinalidade(models.Model):
    """Liga os tipos de documentos às finalidades que os exigem (ou aceitam)."""

    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    finalidade = models.ForeignKey(Finalidade, on_delete=models.PROTECT)
    obrigatorio = models.BooleanField(
        default=True,
        db_comment="Se este tipo de documento é obrigatório para esta finalidade",
    )
    ativo = models.BooleanField(
        default=True, db_comment="Se esta relação está atualmente ativa ou não"
    )

    class Meta:
        db_table = "tipos_documentos_para_finalidades"
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "finalidade"],
                name="uk_tipo_documento_finalidade",
            )
        ]


# ---------------------------------------------------------------------------
# Empenhos
# ---------------------------------------------------------------------------


class Empenho(models.Model):
    """
    Reserva de recursos de um centro, em um ano fiscal, para uma finalidade
    principal. Um empenho tem uma e apenas uma natureza (regra 10); pode pagar
    finalidades diferentes da principal, desde que da mesma natureza (regra 11).

    ``empenho_origem`` liga o empenho de um ano ao do ano anterior de cujo saldo ele
    partiu (regra 16).
    """

    numero_empenho = models.CharField(max_length=32)
    numero_pen = models.CharField(max_length=32, unique=True, null=True, blank=True)
    centro = models.ForeignKey(
        "entidades.Centro", on_delete=models.PROTECT, related_name="empenhos"
    )
    ano_fiscal = models.PositiveSmallIntegerField()
    natureza = models.ForeignKey(
        Natureza, on_delete=models.PROTECT, related_name="empenhos"
    )
    finalidade = models.ForeignKey(
        Finalidade, on_delete=models.PROTECT, related_name="empenhos"
    )
    empenho_origem = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sucessores",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    history = _historico()

    class Meta:
        db_table = "empenhos"
        constraints = [
            models.UniqueConstraint(
                fields=["ano_fiscal", "numero_empenho"], name="uk_empenho_ano_numero"
            )
        ]

    def __str__(self) -> str:
        return f"{self.numero_empenho}/{self.ano_fiscal}"

    def clean(self):
        if self.finalidade_id and self.natureza_id:
            if self.finalidade.natureza_id != self.natureza_id:
                raise ValidationError(
                    "A natureza do empenho precisa ser a mesma da sua finalidade."
                )
        if self.empenho_origem_id:
            origem = self.empenho_origem
            if origem.centro_id != self.centro_id:
                raise ValidationError("O empenho de origem é de outro centro.")
            if origem.ano_fiscal != self.ano_fiscal - 1:
                raise ValidationError(
                    "O empenho de origem precisa ser do ano fiscal imediatamente anterior."
                )
            if origem.natureza_id != self.natureza_id:
                raise ValidationError("O empenho de origem tem outra natureza.")
            if origem.finalidade_id != self.finalidade_id:
                raise ValidationError("O empenho de origem tem outra finalidade.")
            if not origem.finalidade.permite_transporte:
                raise ValidationError(
                    "A finalidade deste empenho não permite carregar saldo para o ano "
                    "seguinte: o saldo deve ser devolvido à PROPLAN."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def saldo(self) -> Decimal:
        """Saldo atual do empenho (soma das linhas do razão)."""
        total = Lancamento.objects.filter(empenho=self).aggregate(t=Sum("montante"))
        return total["t"] or ZERO

    @property
    def gasto(self) -> Decimal:
        total = Lancamento.objects.filter(
            empenho=self, tipo_movimento__conta_como_gasto=True
        ).aggregate(t=Sum("montante"))
        return -(total["t"] or ZERO)


# ---------------------------------------------------------------------------
# Razão
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Definicao:
    nome: str
    altera_total: bool
    conta_como_gasto: bool
    empenho: str  # "obrigatorio" | "proibido" | "livre"
    unidade: str


class TipoMovimento(models.Model):
    """
    Tipo de movimento de uma linha do razão. O que cada tipo faz (se muda o total do
    centro, se conta como gasto, se exige ou proíbe empenho/unidade) está em
    ``DEFINICOES``; a tabela guarda só o suficiente para os relatórios filtrarem.
    Os registros são criados sob demanda por ``TipoMovimento.obter``.
    """

    class Codigo(models.TextChoices):
        CREDITO_ORDINARIO = "credito_ordinario", "Crédito ordinário"
        CREDITO_EXTRAORDINARIO = "credito_extraordinario", "Crédito extraordinário"
        REFORCO_EMPENHO = "reforco_empenho", "Reforço de empenho"
        DISTRIBUICAO = "distribuicao", "Distribuição para unidade"
        PAGAMENTO = "pagamento", "Pagamento de despesa"
        DEBITO_ADMINISTRATIVO = "debito_administrativo", "Débito administrativo"
        CONVERSAO_NATUREZA = "conversao_natureza", "Conversão de natureza"
        TRANSPORTE_SAIDA = "transporte_saida", "Transporte de saldo (saída)"
        TRANSPORTE_ENTRADA = "transporte_entrada", "Transporte de saldo (entrada)"
        DEVOLUCAO_PROPLAN = "devolucao_proplan", "Devolução à PROPLAN"

    DEFINICOES = {
        Codigo.CREDITO_ORDINARIO: _Definicao(
            "Crédito ordinário", True, False, "proibido", "proibido"
        ),
        Codigo.CREDITO_EXTRAORDINARIO: _Definicao(
            "Crédito extraordinário", True, False, "proibido", "proibido"
        ),
        Codigo.REFORCO_EMPENHO: _Definicao(
            "Reforço de empenho", False, False, "obrigatorio", "proibido"
        ),
        Codigo.DISTRIBUICAO: _Definicao(
            "Distribuição para unidade", False, False, "proibido", "obrigatorio"
        ),
        Codigo.PAGAMENTO: _Definicao(
            "Pagamento de despesa", True, True, "obrigatorio", "livre"
        ),
        Codigo.DEBITO_ADMINISTRATIVO: _Definicao(
            "Débito administrativo", True, True, "obrigatorio", "obrigatorio"
        ),
        Codigo.CONVERSAO_NATUREZA: _Definicao(
            "Conversão de natureza", True, False, "obrigatorio", "livre"
        ),
        Codigo.TRANSPORTE_SAIDA: _Definicao(
            "Transporte de saldo (saída)", True, False, "obrigatorio", "livre"
        ),
        Codigo.TRANSPORTE_ENTRADA: _Definicao(
            "Transporte de saldo (entrada)", True, False, "obrigatorio", "proibido"
        ),
        Codigo.DEVOLUCAO_PROPLAN: _Definicao(
            "Devolução à PROPLAN", True, True, "livre", "livre"
        ),
    }

    codigo = models.CharField(max_length=48, unique=True, choices=Codigo.choices)
    nome = models.CharField(max_length=128)
    altera_total = models.BooleanField()
    conta_como_gasto = models.BooleanField(default=False)

    class Meta:
        db_table = "tipos_movimentos"

    def __str__(self) -> str:
        return self.nome

    @classmethod
    def definicao(cls, codigo: str) -> _Definicao:
        return cls.DEFINICOES[cls.Codigo(codigo)]

    @classmethod
    def obter(cls, codigo: str) -> "TipoMovimento":
        definicao = cls.definicao(codigo)
        tipo, _ = cls.objects.get_or_create(
            codigo=str(codigo),
            defaults={
                "nome": definicao.nome,
                "altera_total": definicao.altera_total,
                "conta_como_gasto": definicao.conta_como_gasto,
            },
        )
        return tipo


class Transacao(models.Model):
    """
    Cabeçalho de um conjunto de lançamentos: quem fez, quando, por quê. Nunca é
    editada; uma correção é outra ``Transacao`` apontando para a original em
    ``corrige``.
    """

    class Operacao(models.TextChoices):
        CREDITO = "credito", "Crédito"
        REFORCO = "reforco", "Reforço de empenho"
        DISTRIBUICAO = "distribuicao", "Distribuição entre unidades"
        DESPESA = "despesa", "Despesa"
        DEBITO_ADMINISTRATIVO = "debito_administrativo", "Débito administrativo"
        CONVERSAO = "conversao", "Conversão de natureza"
        LISTA_SIAFI = "lista_siafi", "Pagamento de Lista SIAFI"
        FECHAMENTO = "fechamento", "Fechamento de exercício"
        REABERTURA = "reabertura", "Reabertura de exercício"
        CORRECAO = "correcao", "Correção"

    operacao = models.CharField(max_length=32, choices=Operacao.choices)
    data = models.DateField(help_text="Data do fato registrado")
    usuario = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.PROTECT, related_name="transacoes"
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    justificativa = models.TextField(blank=True)
    corrige = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="correcoes",
    )
    estimada = models.BooleanField(
        default=False,
        help_text="Valor ainda estimado (ex.: diárias antes das notas fiscais chegarem)",
    )
    beneficiario = models.ForeignKey(
        "entidades.Pessoa",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transacoes_beneficiadas",
        help_text="Servidor, aluno, professor ou pessoa externa",
    )

    class Meta:
        db_table = "transacoes"
        indexes = [models.Index(fields=["data"])]

    def __str__(self) -> str:
        return f"#{self.pk} {self.get_operacao_display()} {self.data}"

    def lancamentos_vigentes(self):
        """Linhas desta transação que não são estornos (o que ela 'afirma')."""
        return self.lancamentos.filter(estorna__isnull=True)


class LancamentoQuerySet(models.QuerySet):
    """O razão é imutável: nada de update/delete em massa."""

    def update(self, **kwargs):
        raise ImutavelError("Lançamentos são imutáveis: corrija com estorno.")

    def delete(self):
        raise ImutavelError("Lançamentos não podem ser apagados: corrija com estorno.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ImutavelError("Lançamentos são imutáveis: corrija com estorno.")


class Lancamento(models.Model):
    """
    Uma linha do razão. ``montante`` tem sinal (positivo entra, negativo sai).
    Veja o docstring do módulo para o significado de ``empenho``, ``unidade`` e
    ``tipo_movimento.altera_total``.
    """

    transacao = models.ForeignKey(
        Transacao, on_delete=models.PROTECT, related_name="lancamentos"
    )
    tipo_movimento = models.ForeignKey(
        TipoMovimento, on_delete=models.PROTECT, related_name="lancamentos"
    )
    centro = models.ForeignKey(
        "entidades.Centro", on_delete=models.PROTECT, related_name="lancamentos"
    )
    ano_fiscal = models.PositiveSmallIntegerField()
    natureza = models.ForeignKey(
        Natureza, on_delete=models.PROTECT, related_name="lancamentos"
    )
    empenho = models.ForeignKey(
        Empenho,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lancamentos",
    )
    unidade = models.ForeignKey(
        "entidades.Unidade",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lancamentos",
    )
    finalidade = models.ForeignKey(
        Finalidade,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lancamentos",
        help_text="Para onde o dinheiro foi (pode diferir da finalidade principal do empenho)",
    )
    montante = models.DecimalField(max_digits=15, decimal_places=2)
    estorna = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="estornado_por",
        help_text="Linha que esta linha anula",
    )

    objects = LancamentoQuerySet.as_manager()

    class Meta:
        db_table = "lancamentos"
        constraints = [
            models.CheckConstraint(
                condition=~Q(montante=0), name="ck_lancamento_montante_nao_zero"
            )
        ]
        indexes = [
            models.Index(fields=["empenho"]),
            models.Index(fields=["unidade", "ano_fiscal", "natureza"]),
            models.Index(fields=["centro", "ano_fiscal", "natureza"]),
        ]

    def __str__(self) -> str:
        return f"{self.tipo_movimento_id} {self.montante}"

    def validar(self):
        if self.montante == 0:
            raise ValidationError("Lançamento com montante zero não faz sentido.")
        definicao = TipoMovimento.definicao(self.tipo_movimento.codigo)
        for nome, valor, regra in (
                ("empenho", self.empenho_id, definicao.empenho),
                ("unidade", self.unidade_id, definicao.unidade),
        ):
            if regra == "obrigatorio" and valor is None:
                raise ValidationError(
                    f"'{definicao.nome}' exige {nome}"
                    + (" (toda despesa precisa de empenho)." if nome == "empenho" else ".")
                )
            if regra == "proibido" and valor is not None:
                raise ValidationError(f"'{definicao.nome}' não pode ter {nome}.")
        if self.empenho_id:
            empenho = self.empenho
            if empenho.centro_id != self.centro_id:
                raise ValidationError("O empenho pertence a outro centro.")
            if empenho.ano_fiscal != self.ano_fiscal:
                raise ValidationError(
                    "O ano fiscal do lançamento difere do ano fiscal do empenho."
                )
            if empenho.natureza_id != self.natureza_id:
                raise ValidationError(
                    "Não é possível usar recursos de uma natureza em um empenho de "
                    "outra natureza."
                )
        if self.unidade_id and self.unidade.centro_id != self.centro_id:
            raise ValidationError("A unidade pertence a outro centro.")
        if self.finalidade_id and self.finalidade.natureza_id != self.natureza_id:
            raise ValidationError(
                "Não é possível pagar uma despesa de uma natureza com recursos de outra."
            )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImutavelError("Lançamentos são imutáveis: corrija com estorno.")
        self.validar()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImutavelError("Lançamentos não podem ser apagados: corrija com estorno.")


class ValorDocumento(models.Model):
    """
    Valor de um documento/campo de uma transação (nota fiscal, trecho...). A
    correção de uma transação copia os valores para a nova transação, com as
    alterações. ``ordem`` permite repetir o campo (uma passagem com vários trechos).
    """

    transacao = models.ForeignKey(
        Transacao, on_delete=models.PROTECT, related_name="documentos"
    )
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    ordem = models.PositiveSmallIntegerField(default=0)
    valor = models.CharField(max_length=256)

    class Meta:
        db_table = "valores_documentos"
        ordering = ["tipo_documento_id", "ordem"]
        constraints = [
            models.UniqueConstraint(
                fields=["transacao", "tipo_documento", "ordem"],
                name="uk_valor_documento_ordem",
            )
        ]


class ExercicioCentro(models.Model):
    """Estado (aberto/fechado) de um ano fiscal para um centro."""

    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        FECHADO = "fechado", "Fechado"

    centro = models.ForeignKey(
        "entidades.Centro", on_delete=models.PROTECT, related_name="exercicios"
    )
    ano_fiscal = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ABERTO
    )
    transacao_fechamento = models.ForeignKey(
        Transacao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "exercicios_centros"
        constraints = [
            models.UniqueConstraint(
                fields=["centro", "ano_fiscal"], name="uk_exercicio_centro_ano"
            )
        ]

    def __str__(self) -> str:
        return f"{self.centro_id}/{self.ano_fiscal} ({self.status})"


# ---------------------------------------------------------------------------
# Bolsas e Lista SIAFI
# ---------------------------------------------------------------------------


class VinculoBolsa(models.Model):
    """Vínculo de vários meses entre um bolsista e uma subunidade."""

    bolsista = models.ForeignKey(
        "entidades.Pessoa", on_delete=models.PROTECT, related_name="vinculos_bolsa"
    )
    unidade = models.ForeignKey(
        "entidades.Unidade", on_delete=models.PROTECT, related_name="vinculos_bolsa"
    )
    finalidade = models.ForeignKey(
        Finalidade, on_delete=models.PROTECT, related_name="vinculos_bolsa"
    )
    valor_mensal = models.DecimalField(max_digits=15, decimal_places=2)
    inicio = models.DateField()
    fim = models.DateField()

    history = _historico()

    class Meta:
        db_table = "vinculos_bolsas"
        constraints = [
            models.CheckConstraint(
                condition=Q(fim__gte=models.F("inicio")), name="ck_vinculo_fim_apos_inicio"
            ),
            models.CheckConstraint(
                condition=Q(valor_mensal__gt=0), name="ck_vinculo_valor_positivo"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.bolsista} @ {self.unidade} ({self.inicio}..{self.fim})"

    def clean(self):
        pessoa = self.bolsista
        if pessoa.pessoa_sie_id is None:
            raise ValidationError(
                "Apenas pessoas que já existem no SIE podem ser bolsistas."
            )
        if not (
                Servidor.objects.filter(pessoa=pessoa).exists()
                or Discente.objects.filter(pessoa=pessoa).exists()
        ):
            raise ValidationError(
                "Apenas servidores, professores e alunos do SIE podem ser bolsistas."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class ParcelaBolsa(models.Model):
    """
    Uma competência (mês) de um vínculo. É a unidade de alocação: o ano fiscal vem da
    competência, então um vínculo que atravessa a virada do ano consome o orçamento
    de cada ano na sua parte.

    ``PREVISTA``: ainda sem reserva (ex.: ano futuro sem orçamento distribuído);
    ``ALOCADA``: reserva saldo da subunidade (plano, fora do razão);
    ``PAGA``: paga via Lista SIAFI; ``CANCELADA``: libera a reserva.
    """

    class Status(models.TextChoices):
        PREVISTA = "prevista", "Prevista"
        ALOCADA = "alocada", "Alocada"
        PAGA = "paga", "Paga"
        CANCELADA = "cancelada", "Cancelada"

    vinculo = models.ForeignKey(
        VinculoBolsa, on_delete=models.PROTECT, related_name="parcelas"
    )
    competencia = models.DateField(help_text="Sempre o primeiro dia do mês")
    ano_fiscal = models.PositiveSmallIntegerField(editable=False)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PREVISTA
    )
    empenho_previsto = models.ForeignKey(
        Empenho,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="parcelas_previstas",
        help_text="Empenho que deve pagar esta parcela (base do alerta de complemento)",
    )

    history = _historico()

    class Meta:
        db_table = "parcelas_bolsas"
        constraints = [
            models.UniqueConstraint(
                fields=["vinculo", "competencia"], name="uk_parcela_vinculo_competencia"
            )
        ]
        indexes = [models.Index(fields=["status", "ano_fiscal"])]

    def __str__(self) -> str:
        return f"{self.vinculo_id} {self.competencia:%Y-%m} ({self.status})"

    def save(self, *args, **kwargs):
        self.competencia = self.competencia.replace(day=1)
        self.ano_fiscal = self.competencia.year  # ano fiscal = ano civil
        super().save(*args, **kwargs)


class ListaSIAFI(models.Model):
    """
    Agrupamento mensal de parcelas que são pagas juntas. Estados: rascunho e paga.
    Ao confirmar o pagamento (``services.pagar_lista``) gera todos os lançamentos de
    uma vez; ``numero_siafi`` é a chave de conciliação com o outro sistema.
    """

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        PAGA = "paga", "Paga"

    centro = models.ForeignKey(
        "entidades.Centro", on_delete=models.PROTECT, related_name="listas_siafi"
    )
    competencia = models.DateField(help_text="Sempre o primeiro dia do mês")
    ano_fiscal = models.PositiveSmallIntegerField(editable=False)
    numero_siafi = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.RASCUNHO
    )
    transacao = models.OneToOneField(
        Transacao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lista_siafi",
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    history = _historico()

    class Meta:
        db_table = "listas_siafi"

    def __str__(self) -> str:
        return f"Lista {self.numero_siafi or '(rascunho)'} {self.competencia:%Y-%m}"

    def save(self, *args, **kwargs):
        self.competencia = self.competencia.replace(day=1)
        self.ano_fiscal = self.competencia.year
        super().save(*args, **kwargs)

    @property
    def total(self) -> Decimal:
        return self.itens.aggregate(t=Sum("valor"))["t"] or ZERO


class ItemListaSIAFI(models.Model):
    """Uma parcela dentro de uma Lista SIAFI (cada parcela entra em uma lista só)."""

    lista = models.ForeignKey(ListaSIAFI, on_delete=models.CASCADE, related_name="itens")
    parcela = models.OneToOneField(
        ParcelaBolsa, on_delete=models.PROTECT, related_name="item_lista"
    )
    valor = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = "itens_listas_siafi"
