from rest_framework.response import Response
from rest_framework import status

from despesas.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils import response


class NaturezaFinalidadeView(APIView):
    def get(self, request):
        naturezas_finalidades = NaturezaFinalidade.objects.filter(ativo=True)
        serializer = NaturezaFinalidadeSerializer(naturezas_finalidades, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            serializer = NaturezaFinalidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Natureza de Finalidade adicionada com sucesso.")
        except Exception as e:

            return response.error_server()


class SingleNaturezaFinalidadeView(APIView):
    name = "Natureza de Finalidade"

    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            natureza_finalidade = NaturezaFinalidade.objects.filter(pk=pk, ativo=True).first()
            if not natureza_finalidade:
                return response.not_found(f"{self.name} não encontrado")
            serializer = NaturezaFinalidadeSerializer(natureza_finalidade)
            return Response(serializer.data)
        except Exception as e:

            return response.error_server()

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            natureza_finalidade = NaturezaFinalidade.objects.filter(pk=pk).first()
            if not natureza_finalidade:
                return response.not_found(f"{self.name} não encontrada.")

            serializer = NaturezaFinalidadeSerializer(instance=natureza_finalidade, data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success(f"{self.name} alterada com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            natureza_finalidade = NaturezaFinalidade.objects.filter(pk=pk, ativo=True).first()
            if not natureza_finalidade:
                return response.not_found(f"{self.name} não encontrada.")

            natureza_finalidade.ativo = False
            return response.success(f"{self.name} desativado com sucesso.")

        except Exception as e:
            return response.error_server()


class TipoFinalidadeView(APIView):
    def get(self, request):
        tipos = TipoFinalidade.objects.filter(ativo=True)
        serializer = TipoFinalidadeSerializer(tipos, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            serializer = TipoFinalidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Tipo de Finalidade adicionado com sucesso.")

        except Exception as e:
            print(e)
            return response.error_server()


class SingleTipoFinalidadeView(APIView):
    name = "Tipo de Finalidade"

    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            data = TipoFinalidade.objects.filter(pk=pk, ativo=True).first()
            if not data:
                return response.not_found(f"{self.name} não encontrada.")

            serializer = TipoFinalidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return response.error_server()

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            tipo_finalidade = TipoFinalidade.objects.filter(pk=pk).first()
            if not tipo_finalidade:
                return response.not_found(f"{self.name} não encontrada.")

            serializer = TipoFinalidadeSerializer(instance=tipo_finalidade, data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success(f"{self.name} alterada com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            tipo_finalidade = TipoFinalidade.objects.filter(pk=pk, ativo=True).first()
            if not tipo_finalidade:
                return response.not_found(f"{self.name} não encontrada.")

            tipo_finalidade.ativo = False

            return response.success(f"{self.name} desativada com sucesso.")

        except Exception as e:
            print(e)
            return response.error_server()


class SingleFinalidadeView(APIView):
    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            data = Finalidade.objects.filter(pk=pk, ativo=True).first()
            if not data:
                return response.not_found("Finalidade não encontrada.")
            serializer = FinalidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return response.error_server()

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            finalidade = Finalidade.objects.filter(pk=pk).first()
            if not finalidade:
                return response.not_found("Finalidade não encontrada.")

            serializer = FinalidadeSerializer(
                instance=finalidade,
                data=request.data,
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)

            serializer.save()

            return response.success("Finalidade alterada com sucesso.")

        except Exception as e:
            return response.error_server()

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            finalidade = Finalidade.objects.filter(pk=pk, ativo=True).first()
            if not finalidade:
                return response.not_found("Finalidade não encontrada.")
            finalidade.ativo = False

            return response.success("Finalidade desativada com sucesso.")

        except Exception as e:
            return response.error_server()


class FinalidadesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Finalidade.objects.filter(ativo=True)
        serializer = FinalidadeSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            serializer = FinalidadeSerializer(data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Finalidade criada com sucesso.")

        except Exception as error:
            return response.error_server(error)


class SubunidadeView(APIView):
    def get(self, request):
        try:
            subunidades = Subunidade.objects.filter(ativo=True)
            serializer = SubunidadeSerializer(subunidades, many=True)
            return response.success_data(serializer.data)

        except Exception as e:
            return response.error_server(e)

    def post(self, request):
        try:
            serializer = SubunidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()
            return response.success("Subunidade adicionada com sucesso.")
        except Exception as e:
            return response.error_server(e)


class SingleSubunidadeView(APIView):
    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            data = Subunidade.objects.filter(pk=pk, ativo=True).first()
            if not data:
                return response.not_found("Subunidade não encontrada.")
            serializer = SubunidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return response.error_server(e)

    def patch(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            subunidade = Subunidade.objects.filter(pk=pk).first()
            if not subunidade:
                return response.not_found("Subunidade não encontrada.")

            serializer = SubunidadeSerializer(instance=subunidade, data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Subunidade alterada com sucesso.")

        except Exception as e:
            return response.error_server()

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            subunidade = Subunidade.objects.filter(pk=pk, ativo=True).first()
            if not subunidade:
                return response.not_found("Subunidade não encontrada.")
            subunidade.ativo = False

            return response.success("Subunidade desativada com sucesso.")

        except Exception as e:
            return response.error_server()
