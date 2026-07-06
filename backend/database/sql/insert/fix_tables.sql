INSERT INTO tabelas_finalidades(id_tabela_finalidade, tabela_finalidade) Values
(1,'bolsas'),
(2,'diarias'),
(3,'grafica'),
(4,'hospedagem'),
(5,'manutencao'),
(6,'passagens'),
(7,'refeicoes');

INSERT INTO finalidades (id_finalidade, id_tabela_finalidade, finalidade) VALUES
(1,2, 'Diárias'),
(2,6, 'Passagens aéreas'),
(3,6, 'Passagem rodoviária'),
(4,null,'Almoxarifado'),
(5,7,'Refeições - Hotel'),
(6,3, 'Gráfica'),
(7,4,'Hospedagem - Business'),
(8,4,'Hospedagem - Premium'),
(9,5,'Manutenção'),
(10,null,'Combustível + Manutenção'),
(11,null, 'Correios'),
(12,1,'Bolsas - 2A'),
(13,1,'Bolsas Formação'),
(14,1,'Bolsas - Monitoria'),
(15,1,'Bolsas BAE PRAE PNAES Cód 2CCSH'),
(16,1,'Bolsas BAE PRAE GLOBAL  Cód 22CCSH'),
(17,1,'Bolsas Descubra'),
(18,1,'Bolsas Pró-Revistas'),
(19,1,'Bolsas Eventuais Rec. Extraorçamentário'),
(20,null,'Taxa de Inscrição/Publicação'),
(21,null,'Permanente - Equipamentos'),
(22,null,'Permanente - Móveis'),
(23,null,'Investimentos - Obras'),
(24,null,'Suprimento de Fundos');
-- (26,null,'Transferência - Custeio'),
-- (27,null,'Transferência - Capital / Investimentos');


INSERT INTO tipos_documentos(id_tipo_documento, tipo_documento) VALUES
(2,'PEN'),
(3,'orçamento'),
(5,'ordem de trânsito');

INSERT INTO status(id_status, status) VALUES
(1,'confirmado'),
(2,'pendente'),
(3,'cancelado');

INSERT INTO tipos_transacoes(id_tipo_transacao, tipo_transacao) VALUES
(1,'empenho'),
(2,'despesa'),
(3,'receita');

-- Usuários criados apenas para testes...
-- Dinâmico
INSERT INTO usuarios(username,password,email,administrador)  VALUES ('leandro', 'aleatorio', 'leandronascimento753@gmail.com', True);

INSERT INTO usuarios(username,password,email)  VALUES ('domenico', 'asdas', 'domenico@gmail.com');

