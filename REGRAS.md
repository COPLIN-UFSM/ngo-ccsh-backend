# Regras de negócio

O software consiste em um sistema de contabilidade de centros universitários.

## Despesas

1. Todas as transações pertencem obrigatoriamente a um centro, e um centro apenas.
2. Um centro possui um ano fiscal. Um ano fiscal possui um orçamento previsto (o que é recebido da PROPLAN), os gastos
   efetivados no ano (descritos por lançamentos), e um saldo (orçamento menos soma dos lançamentos).
3. O orçamento de um centro é visualizado em duas dimensões: dimensão de empenhos e dimensão de unidades. Na
   dimensão de empenho, um centro (e.g. CCSH, CT, CCS, etc) recebe recursos da PROPLAN, e os mantém sob sua tutela. O
   centro então empenha (reserva) recursos para certas despesas (e.g. pagamento de bolsas), ou, para despesas que não
   precisam de empenho, simplesmente faz o pagamento da despesa (e.g. paga uma nota fiscal).
    * Na implementação atual, toda despesa precisa de empenho, inclusive as que não dependem de um empenho específico no
      processo externo (e.g. gastos com a gráfica universitária). O empenho é necessário para manter a prestação de
      contas e o saldo reservado consistentes.
4. É possível que um centro receba recursos além do que foi previsto inicialmente no ano. O tipo de transferência de
   recurso deve especificar se é uma transferência ordinária ou extraordinária. 
5. Um empenho pode ser reforçado (receber mais recursos) e debitado, seja porque despesas foram pagas ou porque ele teve
   recursos realocados.
6. Na dimensão de unidades, o centro distribui os recursos entre suas "subunidades" (que também são unidades, mas aqui
   estão denominadas por "subunidades" para deixar clara a relação hierárquica). Esses recursos não são distribuídos _de
   fato_; é como se o centro distribuísse cheques para as subunidades, e depois as subunidades pedem para que o centro
   pague suas despesas com esse cheque. Mas quem paga de fato é o centro.
7. Uma subunidade pode transferir recursos para outra subunidade. Nesse caso, existe uma transação, "transferência", que
   gera dois lançamentos, um crédito e um débito.
8. Existem quatro naturezas de recursos, com a possibilidade de adições futuras: "capital", "custeio", "bolsas PROGRAD", 
   e "bolsas PRAE".
9. Uma finalidade é um propósito para o qual o dinheiro foi gasto. Por exemplo: "Obras" são de capital; "bolsas 2A" são 
   de custeio; bolsas BSE são "bolsas PRAE"; etc.
   * Capital geralmente se refere a compra de equipamentos de uso permanente (e.g. computadores) e obras. Custeio é todo 
     resto (bolsas 2A, bolsas monitoria, gráfica, almoxarifado, combustíveis, passagens aéreas, etc). A única exceção são
   as "Bolsas PRAE" e "Bolsas PROGRAD", que repetem as naturezas (existe uma finalidade "Bolsas PROGRAD" para a natureza
   "Bolsas PROGRAD", e a mesma coisa para "Bolsas PRAE").
   * Os tipos de gasto são chamados de Finalidades. Cada finalidade possui apenas um tipo de natureza.
10. Uma finalidade pode fazer parte de um grupo, para facilitar a visualização em painéis. Por exemplo, todas as bolsas
    podem pertencer ao grupo "bolsas". Especificar um grupo para uma finalidade é opcional.
11. É possível converter recursos de uma natureza para outra, mas isso deve ser feito em uma operação específica 
    (conversão).
12. Não é possível pagar uma despesa (finalidade) de uma natureza com recursos de outra natureza.
13. Algumas despesas criam empenhos específicos (por exemplo, obras - cada obra tem seu próprio empenho). Já outras
    despesas reaproveitam empenhos já criados (por exemplo, Bolsas 2A, que são da natureza custeio).
14. Um empenho possui uma e apenas uma natureza.
15. O ideal seria que um empenho possuísse apenas uma finalidade, porém é comum que bolsas 2A sejam pagas com empenhos
    de Bolsas Monitoria, por exemplo.
16. Na verdade, bolsas são um caso especial. Um bolsista estabelece um vínculo de vários meses com uma subunidade (por
    exemplo, 12 meses). Os recursos para pagar um bolsista são oriundos dos recursos da subunidade, porém é necessário
    que também tenha recursos disponíveis em um empenho. Para cada mês, é montada uma Lista SIAFI, que relaciona quais
    bolsistas serão pagos naquele mês, e quanto deve ser pago para cada um. Geralmente essa Lista SIAFI é paga com
    recursos de apenas um empenho, mas no fim do ano, caso não haja recursos em um empenho, ela é completada com
    recursos de outro empenho (e.g. Empenho 039 para bolsas 2A é somado com Empenho 040 de Bolsas Monitoria).
17. É desejável que, quando souber o prazo de relacionamento de um bolsista, o recurso fique pré-alocado, tanto no
    empenho quando na subunidade. Porém, é desejável também que o recurso possa ser liberado caso a bolsa seja
    cancelada, por qualquer motivo.
18. É necessário manter um registro das transações feitas no sistema, de maneira que se permita ter contabilidade de
    quem fez o quê, e quando.
19. É preciso adicionar atributo de ano fiscal no empenho e no orçamento das subunidades.
20. Para um novo ano fiscal, é possível que um empenho seja criado com saldo de um empenho de mesma finalidade do ano
    anterior. A isso dá-se o nome de transporte.
21. Nem todo empenho permite o carregamento de saldo do ano anterior. Caso sobre dinheiro em alguns tipos de empenho,
    ele deve ser devolvido à PROPLAN. Esses são os dois únicos casos (carrega para o próximo ano ou devolve à PROPLAN,
    que é um gasto).

## Detalhes da implementação de despesas

1. As tabelas internas da aplicação são `managed=False`: o Django não cria nem altera essas tabelas. A estrutura é
   mantida em DDL Db2 versionado em `backend/database/sql/create/`, aplicado manualmente. As views `v_sie_*` são do SIE
   e permanecem somente leitura. Os DDLs dessa pasta são para criar um schema vazio; não substituem um plano de migração
   de um banco legado.
2. O saldo não é armazenado em empenhos ou unidades. Ele é calculado a partir do razão (`Lancamento`), que é imutável:
   correções são novas transações com lançamentos de estorno e, quando necessário, novos lançamentos. O histórico de
   alterações de cadastros, vínculos e listas é mantido separadamente por `django-simple-history`.
3. Cada lançamento pertence a um centro, ano fiscal e natureza e tem um montante com sinal: valor positivo representa
   entrada e negativo representa saída. Seu tipo de movimento determina se altera o total do centro e se conta como
   gasto. Reforço de empenho e distribuição para unidade transferem saldo dentro do centro, sem alterar o total.
4. Os saldos livres são derivados em cada dimensão: recurso livre do centro é o total menos os lançamentos associados a
   empenhos; recurso não distribuído é o total menos os lançamentos associados a unidades. O saldo de um empenho ou
   unidade é a soma dos seus lançamentos. A validação impede saldo negativo, empenho acima do total disponível,
   distribuição acima do recurso do centro e uso de centro, ano ou natureza incompatíveis.
5. A árvore de unidades é representada por `Unidade.unidade_pai`, não inferida durante as consultas a partir do código
   estruturado. O seed legado procura o ancestral existente mais próximo, preservando a largura de cada segmento do
   código ao procurar o pai. A relação só é criada se esse ancestral pertencer ao mesmo centro; se pertencer a outro
   centro, ou se não existir, a unidade fica sem pai.
6. Parcelas de bolsa têm competência mensal e ano fiscal próprios. A alocação (`alocada`) reserva saldo da unidade, mas
   não cria lançamento nem empenha recursos; o empenho e o pagamento são registrados separadamente no razão. Parcelas
   futuras sem saldo disponível ficam previstas. Cancelar uma parcela alocada libera a reserva.
7. Uma Lista SIAFI agrupa parcelas da mesma competência. O pagamento confirma a lista e registra os lançamentos de
   despesa; o valor de cada item pode ser dividido entre empenhos da mesma natureza quando um empenho não tem saldo
   suficiente. Uma parcela só pode pertencer a uma lista.
8. O fechamento de exercício exige informar o destino de todo saldo remanescente. O saldo pode ser transportado apenas
   para empenho do mesmo centro, natureza e finalidade no ano imediatamente seguinte, se a finalidade permitir
   transporte; os demais saldos são devolvidos à PROPLAN e contam como gasto. O fechamento registra uma transação e
   impede novos lançamentos naquele exercício; a reabertura também é registrada e só é permitida se o saldo transportado
   ainda puder ser revertido.
9. A conversão do catálogo legado usa os IDs 36 e 37 de finalidade para reforço de empenho e os IDs 39 a 44 para
   distribuição; eles não viram finalidades novas. O tipo de documento legado “Lista SIAFI” (ID 2) também não é
   importado como documento, pois listas têm modelo próprio. Como os CSVs não informam a permissão de transporte,
   finalidades migradas recebem `permite_transporte=False`; qualquer exceção precisa ser definida explicitamente.
10. A API atual exige autenticação e oferece cadastros de naturezas, grupos, finalidades, tipos de documento e empenhos;
    criação e consulta de transações; consulta de tipos de movimento; e consulta dos documentos e lançamentos de uma
    transação. As operações de transação são crédito, transferência, reforço, distribuição, despesa, débito
    administrativo e conversão de natureza. A correção é registrada em
    `POST /despesas/transacoes/{id}/corrigir/`; não há edição ou exclusão de lançamentos.
11. O ciclo de bolsas está disponível em `/despesas/vinculos-bolsa/`, `/despesas/parcelas-bolsa/` e
    `/despesas/listas-siafi/`. Vínculos são criados e consultados; suas parcelas são geradas idempotentemente por
    `POST /despesas/vinculos-bolsa/{id}/gerar-parcelas/`. Parcelas são consultadas e alteradas somente pelas ações
    `POST .../{id}/alocar/` e `POST .../{id}/cancelar/`. Listas são criadas com centro e competência, recebem parcelas
    alocadas em `POST /despesas/listas-siafi/{id}/itens/`, permitem remover um item enquanto estiverem em rascunho e são
    confirmadas em `POST /despesas/listas-siafi/{id}/pagar/`, com o número SIAFI e, quando necessário, a divisão do
    valor entre empenhos.
12. O exercício é consultado em `GET /despesas/exercicios/pendencias/?centro={id}&ano_fiscal={ano}`. O resultado informa
    saldos de empenhos, unidades e totais por natureza, parcelas ainda alocadas e o estado do exercício. O fechamento é
    solicitado em `POST /despesas/exercicios/fechar/`, com centro, ano fiscal e destinos dos saldos; a reabertura é
    solicitada em `POST /despesas/exercicios/reabrir/`, com centro, ano fiscal e justificativa. Ambas as operações criam
    transações auditáveis no razão.
13. Os saldos das unidades são consultados em `GET /despesas/unidades/?ano_fiscal={ano}`, agrupados por unidade e
    natureza. Para consultar o histórico de uma unidade, use `GET /despesas/unidades/?id_unidade_interna={id}`; também é
    possível informar ambos os parâmetros. Pelo menos um deles é obrigatório para evitar uma consulta sem limite de ano
    ou unidade.

## Entidades

1. Apenas servidores, alunos e professores que já existem no SIE podem ser bolsistas;

## Usuários

1. Apenas servidores com vínculo ativo podem ser usuários do sistema;