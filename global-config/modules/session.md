## Persistência de Sessão (OBRIGATÓRIO)

O sistema de sessão salva contexto automaticamente a cada arquivo editado. Mas foco, decisões e pendências só ficam salvos se **eu registrar ativamente**.

**REGRA — após cada tarefa significativa concluída, executar:**
```bash
python /Users/felipemaranhao/.claude/scripts/session-focus.py \
  --done "descrição do que foi concluído" \
  --pending "próximo passo imediato" \
  --focus "o que estamos construindo agora"
```

**Gatilhos obrigatórios para chamar o script:**
- Ao concluir qualquer feature, fix ou refactor
- Antes de iniciar uma nova tarefa diferente da anterior
- Ao tomar uma decisão técnica relevante (usar `--decision`)
- Ao final de cada resposta longa que envolveu múltiplas edições

**Em caso de crash/retomada:** O contexto é recuperado da sessão ativa JSON + arquivos tocados. Quanto mais chamadas ao script durante a sessão, mais preciso o contexto de retomada.
