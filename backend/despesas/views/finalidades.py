from rest_framework.response import Response
from rest_framework import status

from despesas.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils import response


class TipoDespesaView(APIView):
    def get(self, request):
        tipos_despesa = TipoDespesa.objects.all()
        serializer = TipoDespesaSerializer(tipos_despesa, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            serializer = TipoDespesaSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Tipo de Despesa adicionada com sucesso.")
        except:
            return response.error_server()


class SingleTipoDespesaView(APIView):
    name = "Tipo de Despesa"

    def get(self, request, pk):
        try:
            tipo_despesa = TipoDespesa.objects.filter(pk=pk).first()
            if not tipo_despesa:
                return response.not_found("Tipo de Despesa não encontrado")
            serializer = TipoDespesaSerializer(tipo_despesa)
            return Response(serializer.data)
        except:
            return response.error_server()

    def put(self, request, pk):
        try:
            tipo_despesa = TipoDespesa.objects.filter(pk=pk).first()
            if not tipo_despesa:
                return response.not_found(f"{self.name} não encontrada.")

            serializer = TipoDespesaSerializer(instance=tipo_despesa, data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success(f"{self.name} alterado com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, pk):
        try:
            tipo_despesa = TipoDespesa.objects.filter(pk=pk).first()
            if not tipo_despesa:
                return response.not_found(f"{self.name} não encontrada.")

            finalidades = Finalidade.objects.filter(tipo_despesa=pk)
            if len(finalidades) > 0:
                return response.bad_request(
                    f"Não é possível remover um {self.name} que tenha filhos"
                )

            tipo_despesa.delete()

            return response.success(f"{self.name} deletado com sucesso.")

        except Exception as e:
            return response.error_server()


class CategoriaFinalidadeView(APIView):
    def get(self, request):
        subtipos = CategoriaFinalidade.objects.all()
        serializer = CategoriaFinalidadeSerializer(subtipos, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            serializer = CategoriaFinalidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Categoria de Finalidade adicionado com sucesso.")

        except Exception as e:
            print(e)
            return response.error_server()


class SingleCategoriaFinalidadeView(APIView):
    name = "Categoria de finalidade"

    def get(self, request, pk):
        try:
            data = CategoriaFinalidade.objects.filter(pk=pk).first()
            if not data:
                return response.not_found(f"{self.name} não encontrada.")

            serializer = CategoriaFinalidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return response.error_server()

    def put(self, request, pk):
        try:
            categoria_finalidade = CategoriaFinalidade.objects.filter(pk=pk).first()
            if not categoria_finalidade:
                return response.not_found(f"{self.name} não encontrada.")

            serializer = CategoriaFinalidadeSerializer(
                instance=categoria_finalidade, data=request.data
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success(f"{self.name} alterado com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, pk):
        try:
            categoria_finalidade = CategoriaFinalidade.objects.filter(pk=pk).first()
            if not categoria_finalidade:
                return response.not_found(f"{self.name} não encontrada.")

            finalidades = Finalidade.objects.filter(categoria_finalidade=pk)
            if len(finalidades) > 0:
                return response.bad_request(
                    f"Não é possível remover uma {self.name} que tenha filhos"
                )

            categoria_finalidade.delete()

            return response.success(f"{self.name} deletada com sucesso.")

        except Exception as e:
            return response.error_server()


class SingleFinalidadeView(APIView):
    def get(self, request, pk):
        try:
            data = Finalidade.objects.filter(pk=pk).first()
            if not data:
                return response.not_found("Finalidade não encontrada.")
            serializer = FinalidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return response.error_server()

    def put(self, request, pk):
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

    def delete(self, request, pk):
        try:
            finalidade = Finalidade.objects.filter(pk=pk).first()
            if not finalidade:
                return response.not_found("Finalidade não encontrada.")
            finalidade.delete()

            return response.success("Finalidade deletada com sucesso.")

        except Exception as e:
            return response.error_server()


class FinalidadesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Finalidade.objects.all()
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
            subunidades = Subunidade.objects.all()
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
    def get(self, request, pk):
        try:
            data = Subunidade.objects.filter(pk=pk).first()
            if not data:
                return response.not_found("Subunidade não encontrada.")
            serializer = SubunidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return response.error_server(e)

    def patch(self, request, pk):
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

    def delete(self, request, pk):
        try:
            subunidade = Subunidade.objects.filter(pk=pk).first()
            if not subunidade:
                return response.not_found("Subunidade não encontrada.")
            subunidade.delete()

            return response.success("Subunidade deletada com sucesso.")

        except Exception as e:
            return response.error_server()
