# NGO CCSH - Documentação da API

Esta documentação detalha os endpoints, métodos e regras de negócio da API do Núcleo de Gestão Orçamentária do CCSH/UFSM.

---

## 🔐 Autenticação (JWT)

A API utiliza JSON Web Tokens (JWT) para autenticação. Todas as requisições (exceto login e recuperação de senha) exigem o header:
`Authorization: Bearer <seu_token>`

### [POST] /users/login/
Autentica um usuário e retorna os tokens de acesso.
- **Payload:**
  ```json
  {
    "username": "seu_usuario",
    "password": "sua_senha"
  }
  ```
- **Resposta (200 OK):**
  ```json
  {
    "refresh": "token_de_atualizacao",
    "token": "token_de_acesso"
  }
  ```

---

## 👤 Módulo de Usuários

### [GET] /users/
Lista todos os usuários ativos. (Requer Autenticação)

### [POST] /users/
Cria um novo usuário. (Apenas Admin)

### [GET/PATCH/DELETE] /users/<int:pk>/
- **GET:** Detalhes de um usuário.
- **PATCH:** Atualiza dados do usuário (Dono ou Admin).
- **DELETE:** Desativa a conta do usuário (Soft Delete).

### [PATCH] /users/permission-update/<int:pk>/
Altera as permissões de superusuário ou staff. (Apenas Admin)
- **Payload:** `{"is_superuser": true}`

### [PATCH] /users/change-password/<int:pk>/
Altera a senha do usuário logado ou de terceiros (se for Admin).

---

## 💰 Módulo de Pagamentos Parciais

### 📜 Empenhos

#### [GET/POST] /partial-payments/empenhos/
- **GET:** Lista todos os empenhos.
- **POST:** Adiciona um novo empenho. (Apenas Admin)

#### [GET/PUT/DELETE] /partial-payments/empenhos/<int:pk>/
- **GET:** Detalhes de um empenho específico.
- **PUT:** Atualiza dados do empenho. (Apenas Admin)
- **DELETE:** Remove o empenho (Apenas se não houver transações vinculadas).

#### [GET] /partial-payments/empenhos/montante-total/<int:pk>/
Retorna o saldo atualizado do empenho.
- **Resposta Exemplo (200 OK):**
  ```json
  {
    "data": {
      "montante_total": 800.00
    }
  }
  ```

#### [GET] /partial-payments/empenhos/transacoes-empenho/<int:pk>/
Lista todas as transações vinculadas a um empenho específico.

### 📑 Tipos de Documento

#### [GET/POST] /partial-payments/tipos-documento/
- **POST:** (Apenas Admin)

#### [GET/PUT/DELETE] /partial-payments/tipos-documento/<int:pk>/
- **DELETE:** Desativa o tipo de documento (Soft Delete).

### 💸 Transações

#### [POST] /partial-payments/transacoes/
Registra uma nova movimentação financeira. (Apenas Admin)
- **Payload:**
  ```json
  {
    "empenho_pai": 1,
    "tipo_documento": 2,
    "eh_credito": true,
    "documento": "NF-2024",
    "descricao": "Aporte inicial",
    "montante": "1500.00"
  }
  ```
- **Regras de Negócio:**
  - Bloqueia lançamentos em empenhos inativos.
  - Bloqueia o uso de tipos de documentos inativos.
  - Impede débitos que excedam o saldo atual do empenho.

#### [GET/PUT/DELETE] /partial-payments/transacoes/<int:pk>/
- **GET:** Detalhes de uma transação, incluindo o campo calculado `saldo_no_momento`.
- **DELETE:** Remove a transação e **recalcula automaticamente** o saldo dos lançamentos posteriores.

---

## 🛠️ Status Codes Padronizados

- **200 OK**: Requisição bem sucedida.
- **201 Created**: Recurso criado com sucesso.
- **204 No Content**: Exclusão realizada com sucesso.
- **400 Bad Request**: Erro de validação ou lógica de negócio (ex: Saldo insuficiente).
- **401 Unauthorized**: Token ausente ou inválido.
- **403 Forbidden**: Usuário autenticado mas sem permissão administrativa.
- **404 Not Found**: Recurso não encontrado.
