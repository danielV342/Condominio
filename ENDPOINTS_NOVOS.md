# Endpoints adicionados (todos exigem `Authorization: Bearer <jwt>`)

| Método | Rota | Quem | O que faz |
|---|---|---|---|
| GET | /perfil | qualquer | Dados do usuário logado |
| PUT | /perfil | qualquer | Altera nome, unidade, telefone, e-mail ("" limpa o campo) |
| POST | /perfil/senha | qualquer | Troca a senha (`senha_atual`, `nova_senha` ≥ 6) |
| GET | /avisos | qualquer | Lista avisos (mais novos primeiro) |
| POST | /avisos | síndico | Publica aviso (`titulo`, `mensagem`, `prioridade` NORMAL/IMPORTANTE/URGENTE) |
| DELETE | /avisos/{id} | síndico | Apaga aviso |
| POST | /chamados | qualquer | Abre manutenção ou ocorrência (`tipo` MANUTENCAO/OCORRENCIA) |
| GET | /chamados/meus | qualquer | Chamados do próprio usuário |
| GET | /chamados?tipo=&status= | síndico | Todos os chamados, com filtros |
| GET | /chamados/resumo | síndico | Quantidade de manutenções/ocorrências em aberto |
| PATCH | /chamados/{id} | síndico | Altera `status` (ABERTO/EM_ANDAMENTO/CONCLUIDO) e `resposta` |
| GET | /condominio | qualquer | Dados do condomínio |
| PUT | /condominio | síndico | Edita dados do condomínio |

Mudanças de segurança: `/moradores`, `/financeiro/dashboard` e `/financeiro/pagamentos/debug`
agora são só do síndico; `/financeiro/cobrancas/{cpf}` só mostra o CPF do próprio morador.

As tabelas `avisos`, `chamados` e `condominio` são criadas sozinhas e as colunas novas de
`usuarios` (email, telefone, unidade) e `pagamentos` (Pix) são adicionadas na inicialização,
sem precisar de `RESET_DATABASE=true`.
