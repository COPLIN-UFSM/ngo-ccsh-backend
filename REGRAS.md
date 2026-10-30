# Regras de negócio

## Despesas

1. Existem duas dimensões: dimensão de empenhos e dimensão de unidades. Na dimensão de empenho, um centro 
   (e.g. CCSH, CT, CCS, etc) recebe recursos da PROPLAN, e os mantém sob sua tutela. O centro então empenha (reserva)
   recursos para certas despesas (e.g. pagamento de bolsas), ou, para despesas que não precisam de empenho, simplesmente
   faz o pagamento da despesa (e.g. paga uma nota fiscal).
   * Está sob discussão se é mais conveniente forçar todas as despesas a possuírem um empenho associado, mesmo aquelas 
     que de fato não precisam de empenho (e.g. gastos com a gráfica universitária)
2. É possível que um centro receba recursos além do que foi previsto inicialmente no ano. O tipo de transferência de 
   recurso deve especificar se é uma transferência ordinária ou extraoridinária.
3. Um empenho pode ser reforçado (receber mais recursos) e debitado, seja porque despesas foram pagas ou porque ele teve
   recursos realocados.
4. Na dimensão de unidades, o centro distribui os recursos entre suas "subunidades" (que também são unidades, mas aqui
   estão denominadas por "subunidades" para deixar clara a relação hierárquica). Esses recursos não são distribuídos 
   _de fato_; é como se o centro distribuísse cheques para as subunidades, e depois as subunidades pedem para que o 
   centro pague suas despesas com esse cheque. Mas quem paga de fato é o centro.
5. Existem quatro naturezas de recursos, com a possibilidade de mais: "capital", "custeio", "bolsas PROGRAD", e 
   "bolsas PRAE".
6. É possível converter recursos de uma natureza para outra, mas isso deve ser feito em uma operação específica. 
7. Não é possível pagar uma despesa de uma natureza com recursos de outra natureza.
8. Capital geralmente se refere a compra de equipamentos de uso permanente (e.g. computadores) e obras. Custeio é todo o 
   resto (bolsas 2A, bolsas monitoria, gráfica, almoxarifado, combustíveis, passagens aéreas, etc). A única exceção são
   as "Bolsas PRAE" e "Bolsas PROGRAD", que repetem as naturezas (existe uma finalidade "Bolsas PROGRAD" para a natureza
   "Bolsas PROGRAD", e a mesma coisa para "Bolsas PRAE").
   * Os tipos de gasto são chamados de Finalidades. Cada finalidade possui apenas um tipo de natureza.
9. Algumas despesas criam empenhos específicos (por exemplo, obras - cada obra tem seu próprio empenho). Já outras 
   despesas reaproveitam empenhos já criados (por exemplo, Bolsas 2A, que são da natureza custeio).
10. Um empenho possui uma e apenas uma natureza.
11. O ideal seria que um empenho possuísse apenas uma finalidade, porém é comum que bolsas 2A sejam pagas com empenhos
    de Bolsas Monitoria, por exemplo.
12. Na verdade, bolsas são um caso especial. Um bolsista estabelece um vínculo de vários meses com uma subunidade 
    (por exemplo, 12 meses). Os recursos para pagar um bolsista são oriundos dos recursos da subunidade, porém é 
    necessário que também tenha recursos disponíveis em um empenho. Para cada mês, é montada uma Lista SIAFI, que 
    relaciona quais bolsistas serão pagos naquele mês, e quanto deve ser pago para cada um. Geralmente essa Lista SIAFI
    é paga com recursos de apenas um empenho, mas no fim do ano, caso não haja recursos em um empenho, ela é completada
    com recursos de outro empenho (e.g. Empenho 039 para bolsas 2A é somado com Empenho 040 de Bolsas Monitoria).
13. É desejável que, quando souber o prazo de relacionamento de um bolsista, o recurso fique pré-alocado, tanto no 
    empenho quando na subunidade. Porém, é desejável também que o recurso possa ser liberado caso a bolsa seja cancelada,
    por qualquer motivo.
14. É necessário manter um registro das transações feitas no sistema, de maneira que permita-se ter contabilidade de 
    quem fez o quê, e quando.
15. É preciso adicionar atributo de ano fiscal no empenho e no orçamento das subunidades.
16. Para um novo ano fiscal, é possível que um empenho seja criado com saldo de um empenho de mesma finalidade do ano 
    anterior.
17. Nem todo empenho permite o carregamento de saldo do ano anterior. Caso sobre dinheiro em alguns tipos de empenho,
    ele deve ser devolvido à PROPLAN. Esses são os dois únicos casos (carrega para o próximo ano ou devolve à PROPLAN, 
    que é um gasto).

## Entidades

1. Apenas servidores, alunos e professores que já existem no SIE podem ser bolsistas;

## Usuários

1. Apenas servidores com vínculo ativo podem ser usuários do sistema;