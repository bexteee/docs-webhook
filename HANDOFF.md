# Handoff — Automação de Documentação (docs-webhook)

**Autor original:** Vitor
**Data de entrega:** 22 de julho de 2026
**Status:** Funcional, testado em produção

## 1. O que este sistema faz

Sempre que uma Pull Request é aprovada e merged na branch `main` do repositório de código, o sistema:

1. Busca o diff da PR via API do GitHub
2. Envia esse diff para a API da Anthropic (Claude), pedindo um resumo técnico em português
3. Adiciona esse resumo ao changelog da documentação (`startup-docs/docs/changelog.md`)
4. Faz commit e push dessa atualização
5. Aciona um webhook que reconstrói o site de documentação (MkDocs) e o publica

Nenhuma etapa exige intervenção manual — do merge da PR até o site atualizado, leva menos de um minuto.

## 2. Arquitetura

```
PR merged (repositório de código)
    → GitHub Action dispara
        → busca diff via API do GitHub
        → chama API da Anthropic para gerar resumo
        → clona startup-docs, atualiza changelog.md
        → commit + push
        → POST autenticado para o webhook

Servidor (DigitalOcean Droplet):
    Nginx (porta 80, público)
        → /deploy repassa para o Gunicorn (127.0.0.1:5000)
        → demais rotas servem o site estático de /var/www/html

    Gunicorn + Flask (gerenciado por systemd, reinicia sozinho se cair)
        → valida o secret do webhook (HMAC)
        → git pull no startup-docs
        → mkdocs build
        → troca atômica do conteúdo publicado (sem downtime perceptível)
```

## 3. Repositórios

| Repositório | Propósito |
|---|---|
| `docs-webhook` | Webhook receiver (Flask) + GitHub Action |
| `startup-docs` | Conteúdo da documentação (MkDocs) |

## 4. Acesso ao servidor

- **Provedor:** DigitalOcean
- **IP público:** 142.93.63.249
- **Acesso:** via SSH, chave pública já associada ao Droplet
- **Ação necessária:** adicionar a chave SSH pública da equipe que assumirá o projeto em `~/.ssh/authorized_keys` no servidor, ou recriar o Droplet com as chaves da equipe

## 5. Secrets e credenciais — ação necessária antes de assumir

Os secrets abaixo foram gerados com credenciais pessoais do desenvolvedor original e **devem ser substituídos** por credenciais próprias da empresa antes de uso continuado:

| Secret | Onde está | O que fazer |
|---|---|---|
| `ANTHROPIC_API_KEY` | GitHub Secret (`docs-webhook`) | Gerar uma chave da API da Anthropic com a conta/billing da empresa, substituir o secret |
| `WEBHOOK_SECRET` | GitHub Secret + `.env` no servidor | Gerar novo valor (`openssl rand -hex 32`), atualizar nos dois lugares, reiniciar o serviço (`sudo systemctl restart docs-webhook`) |
| `STARTUP_DOCS_TOKEN` | GitHub Secret (`docs-webhook`) | Gerar um novo Personal Access Token (fine-grained, permissão de escrita em `startup-docs`) com uma conta institucional, não pessoal |
| Custo do Droplet | DigitalOcean | Transferir para a conta/billing da empresa, ou migrar para infraestrutura própria |

## 6. Operações comuns

**Verificar se o webhook está no ar:**
```bash
sudo systemctl status docs-webhook
```

**Ver logs em caso de erro:**
```bash
sudo journalctl -u docs-webhook -n 50 --no-pager
```

**Reiniciar o serviço** (necessário após qualquer mudança em `.env` ou `app.py`):
```bash
sudo systemctl restart docs-webhook
```

**Testar o webhook manualmente:**
```bash
curl -X POST -H "Authorization: Bearer SEU_SECRET" http://142.93.63.249/deploy
```

## 7. Limitações conhecidas

- A IA gera o resumo a partir apenas do diff da PR, sem contexto mais amplo do projeto — ocasionalmente pode descrever incorretamente o propósito de uma mudança. Recomenda-se revisão humana periódica do changelog gerado.
- O workflow está atualmente configurado para o repositório `docs-webhook` como gatilho de teste. Para uso real, o arquivo `.github/workflows/deploy-docs.yml` deve ser replicado no repositório de código real da aplicação.
- Não há HTTPS configurado — o tráfego roda em HTTP puro. Recomenda-se configurar um certificado SSL (ex: via Certbot/Let's Encrypt) antes de uso em produção contínua.

## 8. Documentação adicional

- `README.md` (em `docs-webhook`) — visão geral técnica e decisões de design