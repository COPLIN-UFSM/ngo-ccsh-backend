CREATE TABLE ORCAMENTO.VERSOES_TRANSACOES (
    id_versao_transacao INTEGER NOT NULL PRIMARY KEY,
    id_transacao INTEGER NOT NULL REFERENCES ORCAMENTO.TRANSACOES(id_transacao),
    numero_versao INTEGER NOT NULL DEFAULT 1,
    id_empenho INTEGER DEFAULT NULL REFERENCES ORCAMENTO.EMPENHOS(id_empenho),
    id_finalidade integer not null references orcamento.FINALIDADES(ID_FINALIDADE),
    id_unidade_credora integer default null references orcamento.unidades(ID_UNIDADE_INTERNA),
    id_unidade_executora integer default null references orcamento.unidades(ID_UNIDADE_INTERNA),
    id_usuario integer not null null references orcamento.usuarios(ID_USUARIO),
    id_status_pagamento integer not null references orcamento.status_pagamentos(ID_STATUS_PAGAMENTO),
    id_beneficiario integer not null references orcamento.pessoas(id_pessoa_interna),
    credito boolean default false,
    montante float not null default 0,
    data_criacao timestamp not null default current_timestamp
);

comment on table ORCAMENTO.VERSOES_TRANSACOES is 'Armazena diferentes versões de uma transação, possuindo um campo para indicar se uma versão é a última.';