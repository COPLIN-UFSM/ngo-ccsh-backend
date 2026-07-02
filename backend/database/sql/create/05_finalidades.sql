CREATE TABLE ORCAMENTO.FINALIDADES (
  id_finalidade INTEGER NOT NULL PRIMARY KEY,
  id_tipo_despesa integer,
  id_categoria_finalidade integer NOT NULL,
  finalidade varchar(255)  NOT NULL
);

ALTER TABLE ORCAMENTO.FINALIDADES ADD CONSTRAINT fk_finalidades_categoria_finalidade  FOREIGN KEY (id_categoria_finalidade) REFERENCES ORCAMENTO.CATEGORIAS_FINALIDADES (id_categoria_finalidade) ENFORCED;
ALTER TABLE ORCAMENTO.FINALIDADES ADD CONSTRAINT fk_finalidades_tipos_despesa FOREIGN KEY (id_tipo_despesa) REFERENCES TIPOS_DESPESA (id_tipo_despesa) ENFORCED ;