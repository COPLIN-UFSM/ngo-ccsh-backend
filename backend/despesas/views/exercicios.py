from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from despesas import saldos, services
from despesas.models import ExercicioCentro
from despesas.serializers import TransacaoReadSerializer
from despesas.serializers_bolsas import (
    FecharExercicioSerializer,
    ReabrirExercicioSerializer,
)
from entidades.models import Centro


class PendenciasQuerySerializer(serializers.Serializer):
    centro = serializers.PrimaryKeyRelatedField(queryset=Centro.objects.all())
    ano_fiscal = serializers.IntegerField(min_value=1, max_value=32767)


def _validation_detail(exc):
    return exc.messages if isinstance(exc, DjangoValidationError) else str(exc)


def _serialize_pendencias(result):
    return {
        "ok": result["ok"],
        "empenhos": [
            {
                "id_empenho": empenho.pk,
                "numero_empenho": empenho.numero_empenho,
                "saldo": str(saldo),
            }
            for empenho, saldo in result["empenhos"]
        ],
        "unidades": [
            {
                "id_unidade": unidade_id,
                "id_natureza": natureza_id,
                "saldo": str(saldo),
            }
            for unidade_id, natureza_id, saldo in result["unidades"]
        ],
        "totais": [
            {"id_natureza": natureza_id, "total": str(total)}
            for natureza_id, total in result["totais"]
        ],
        "parcelas_alocadas": result["parcelas_alocadas"],
    }


class ExercicioCentroViewSet(viewsets.GenericViewSet):
    queryset = ExercicioCentro.objects.select_related(
        "centro", "transacao_fechamento"
    )
    serializer_class = FecharExercicioSerializer
    http_method_names = ["get", "post"]

    @action(detail=False, methods=["get"])
    def pendencias(self, request):
        query = PendenciasQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        centro_id = query.validated_data["centro"].pk
        ano_fiscal = query.validated_data["ano_fiscal"]
        resultado = saldos.pendencias_fechamento(centro_id, ano_fiscal)
        exercicio = self.get_queryset().filter(
            centro_id=centro_id, ano_fiscal=ano_fiscal
        ).first()
        return Response(
            {
                "centro": centro_id,
                "ano_fiscal": ano_fiscal,
                "status": (
                    exercicio.status
                    if exercicio is not None
                    else ExercicioCentro.Status.ABERTO
                ),
                "id_transacao_fechamento": (
                    exercicio.transacao_fechamento_id
                    if exercicio is not None
                    else None
                ),
                **_serialize_pendencias(resultado),
            }
        )

    @action(detail=False, methods=["post"])
    def fechar(self, request):
        serializer = FecharExercicioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        destinos = [
            services.DestinoSaldo(**destino)
            for destino in data["destinos"]
        ]
        try:
            transacao = services.fechar_exercicio(
                data["centro"],
                data["ano_fiscal"],
                request.user,
                destinos,
            )
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            raise ValidationError(_validation_detail(exc)) from exc
        return Response(
            TransacaoReadSerializer(transacao).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def reabrir(self, request):
        serializer = ReabrirExercicioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            transacao = services.reabrir_exercicio(
                data["centro"],
                data["ano_fiscal"],
                request.user,
                data["justificativa"],
            )
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            raise ValidationError(_validation_detail(exc)) from exc
        return Response(
            TransacaoReadSerializer(transacao).data,
            status=status.HTTP_201_CREATED,
        )
