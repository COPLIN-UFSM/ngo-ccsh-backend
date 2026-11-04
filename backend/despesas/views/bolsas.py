from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from despesas import services
from despesas.models import ListaSIAFI, ParcelaBolsa, VinculoBolsa
from despesas.serializers import TransacaoReadSerializer
from despesas.serializers_bolsas import (
    ListaSIAFICreateSerializer,
    ListaSIAFIIncluirParcelasSerializer,
    ListaSIAFIPagamentoSerializer,
    ListaSIAFIReadSerializer,
    ParcelaAlocacaoSerializer,
    ParcelaBolsaSerializer,
    VinculoBolsaSerializer,
)


def _validation_detail(exc):
    return exc.messages if isinstance(exc, DjangoValidationError) else str(exc)


class VinculoBolsaViewSet(viewsets.ModelViewSet):
    queryset = VinculoBolsa.objects.select_related(
        "bolsista", "unidade", "finalidade"
    ).order_by("-inicio", "id_vinculo_bolsa")
    serializer_class = VinculoBolsaSerializer
    http_method_names = ["get", "post"]
    filterset_fields = ["bolsista", "unidade", "finalidade"]

    @action(detail=True, methods=["post"], url_path="gerar-parcelas")
    def gerar_parcelas(self, request, pk=None):
        vinculo = self.get_object()
        parcelas = services.gerar_parcelas(vinculo)
        return Response(
            ParcelaBolsaSerializer(parcelas, many=True).data,
            status=status.HTTP_201_CREATED if parcelas else status.HTTP_200_OK,
        )


class ParcelaBolsaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParcelaBolsa.objects.select_related(
        "vinculo", "vinculo__bolsista", "vinculo__unidade", "empenho_previsto"
    ).order_by("competencia", "id_parcela_bolsa")
    serializer_class = ParcelaBolsaSerializer
    filterset_fields = ["vinculo", "ano_fiscal", "status", "competencia"]

    @action(detail=True, methods=["post"])
    def alocar(self, request, pk=None):
        parcela = self.get_object()
        serializer = ParcelaAlocacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(parcela=parcela)
        return Response(ParcelaBolsaSerializer(updated).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        parcela = self.get_object()
        try:
            updated = services.cancelar_parcela(parcela)
        except (DjangoValidationError, services.RegraDeNegocio) as exc:
            raise ValidationError(_validation_detail(exc)) from exc
        return Response(ParcelaBolsaSerializer(updated).data)


class ListaSIAFIViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        ListaSIAFI.objects.select_related("centro", "transacao")
        .prefetch_related("parcelas__vinculo__bolsista")
        .order_by("-competencia", "id_lista_siafi")
    )
    serializer_class = ListaSIAFIReadSerializer
    filterset_fields = ["centro", "ano_fiscal", "competencia", "status"]
    http_method_names = ["get", "post", "delete"]

    def create(self, request, *args, **kwargs):
        serializer = ListaSIAFICreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lista = serializer.save()
        return Response(
            self.get_serializer(lista).data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )

    @action(detail=True, methods=["post"], url_path="parcelas")
    def incluir_parcelas(self, request, pk=None):
        lista = self.get_object()
        serializer = ListaSIAFIIncluirParcelasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parcelas = serializer.save(lista=lista)
        lista = self.get_queryset().get(pk=lista.pk)
        return Response(
            self.get_serializer(lista).data,
            status=status.HTTP_201_CREATED if parcelas else status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="parcela_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
            )
        ]
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"parcelas/(?P<parcela_id>[^/.]+)",
    )
    def remover_parcela(self, request, pk=None, parcela_id=None):
        lista = self.get_object()
        parcela = get_object_or_404(ParcelaBolsa, pk=parcela_id, lista=lista)
        try:
            services.remover_parcela_da_lista(lista, parcela)
        except services.RegraDeNegocio as exc:
            raise ValidationError(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def pagar(self, request, pk=None):
        lista = self.get_object()
        serializer = ListaSIAFIPagamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transacao = serializer.save(lista=lista, usuario=request.user)
        return Response(
            TransacaoReadSerializer(transacao).data,
            status=status.HTTP_201_CREATED,
        )
