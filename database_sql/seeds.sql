INSERT INTO transacoes(id_transacao,
  id_tipo_transacao, id_transacao_pai, id_finalidade, id_subunidade_credora, id_subunidade_executora, id_usuario,
  id_status, descricao, montante
) 
VALUES
--receita
(1, 3, null, null, 50, 1, 1, 1, 'Proplan enviou o dinheiro.', 100000.50),

--empenhos
--id,tipo, pai, fin, subcred, subexe, user, statat, descri, monta
(2, 1, 1, 12, 1, null, 1, 1, 'Direcao empenhou dinheiro para bolsa 2A.', 2500),
(3, 1, 1, 13, 1, null, 1, 1, 'Direcao empenhou dinheiro para bolsa Formacao.', 2500),
(4, 1, 1, 2, 1, null, 1, 1, 'Direcao empenhou dinheiro para Viagem área.', 5000),
(5, 1, 1, 1, 1, null, 1, 1, 'Direcao empenhou dinheiro para diárias.', 2500),

--id,tipo, pai, fin, subcred, subexe, user, statat, descri, monta
-- gastos previsto, como se fosse uma transferencia de dinheiro.
(6, 2, 1, null, 1, 2, 1, 1, 'CCSH enviou o dinheiro para dep. Adm.', 3000.50),
(7, 2, 1, null, 1, 3, 1, 1, 'Proplan enviou o dinheiro para dep. Contábil', 10000),
(8, 2, 1, null, 1, 6, 1, 1, 'Proplan enviou o dinheiro para dep. Direito.', 3000);

--receita vinda da despesa.
(9, 3, 6, null, 1, 2, 1, 1, 'dep. Adm. recebeu valor', 3000.50),
(10, 3, 7, null, 1, 3, 1, 1, 'dep. Cont. recebeu valor', 10000),
(11, 3, 8, null, 1, 6, 1, 1, 'dep. Direito. recebeu valor', 3000),
-- No pai vai ser uma despesa e no filho uma receita.
--id,tipo, pai, fin, subcred, subexe, user, statat, descri, monta
(10, 2, 11, 2, 6, 6,1,1,'Gastando com viagem', 4000),
(10, 2, 11, 3, 6, 6,1,1,'Gastando com viagem', 4000),


SELECT * from transacoes where tipo_transacao.id_tipo_transacao = 1  and transacoes.finalidade = 1 -- Consigo ver quanto tenho de dinheiro empenhado.
SELECT * from transacoes where transacoes.finalidade = 1 AND transacoes.finalidade = 2 -- consigo ver quanto de dinheiro gastei, basta remover da contar as tranferencias de dinheiro.
-- AND id_finalidade IS NOT NULL



