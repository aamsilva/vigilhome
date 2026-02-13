# VigilHome Use Cases & Features
## Master Plan - Smart Home Intelligence

**Vision:** Transform VigilHome from simple surveillance into an intelligent home awareness system that learns, predicts, and automates.

---

## 🎯 Core Use Cases

### 1. **Smart Presence & Identity**
**Status:** 🔄 In Progress

**Features:**
- ✅ Person detection (YOLO)
- 🔄 Face recognition (dlib/FaceNet) - in progress
- ✅ Family member identification (Augusto, Sofia, Maria Rita, Vicente)
- ✅ Visitor/unknown person detection
- 🔄 Clothing-independent recognition

**Use Cases:**
- "Quem está em casa?" → Augusto na sala, Sofia na cozinha
- Alerta: "Pessoa desconhecida na porta"
- "O Vicente chegou?" → Não, Vicente está nos EUA

---

### 2. **Daily Presence Reports**
**Status:** ✅ Implemented

**Features:**
- Relatório diário automático (08:00)
- Horários de chegada/saída
- Tempo total em casa por pessoa
- Câmaras utilizadas

**Use Cases:**
- "Quantas horas o Augusto esteve em casa ontem?"
- "A Sofia chegou tarde ontem?"
- Comparativos semanais

---

### 3. **Door Entry/Exit Detection**
**Status:** 📋 Planned

**Features:**
- Zona da porta monitorizada
- Tracking de movimento → porta
- Deteção de saída/entrada
- Alertas de não-chegada

**Use Cases:**
- "A Maria Rita saiu de casa às 15:00"
- Alerta: "Sofia não chegou às 19h como habitual"
- "Porta aberta durante 30 min"

---

### 4. **Anomaly Detection & Alerts**
**Status:** 🔄 Training Phase

**Features:**
- Aprendizagem de rotinas normais
- Deteção de comportamentos anómalos
- Alertas inteligentes (poucos mas relevantes)
- Filtro de falsos positivos

**Use Cases:**
- "Movimento na sala às 3h da manhã"
- "Augusto não chegou à hora habitual"
- "Porta da rua aberta durante a noite"
- "Ausência prolongada da casa (fuga de gás, inundação)"

---

### 5. **Smart Home Integration**
**Status:** 📋 Planned

**Features:**
- Controlo de estores/cortinas
- Gestão de luzes
- Controlo de AC/temperatura
- Integração com fechaduras

**Use Cases:**
- **Modo Privacidade:** Pessoa detetada → Estores descem
- **Chegada:** Augusto chega → Luzes ligam, AC liga
- **Ausência:** Casa vazia → Modo eco (luzes off, AC eco)
- **Noite:** 23h → Fechar todos estores automaticamente
- **Cinema:** "Modo cinema" → Fechar estores, luzes off

---

### 6. **Activity Intelligence**
**Status:** 📋 Planned

**Features:**
- Mapa de calor de atividade
- Tempo por cômodo
- Padrões de movimento
- Predição de comportamento

**Use Cases:**
- "Onde o Augusto passa mais tempo?"
- "A Sofia está mais tempo na cozinha esta semana"
- Prever quando alguém vai chegar
- Sugerir optimizações de energia

---

### 7. **Visitor & Security Log**
**Status:** 📋 Planned

**Features:**
- Registo de visitantes
- Foto + timestamp de entrada
- Identificação de padrões (entregas, vizinhos)
- Alertas de pessoas suspeitas

**Use Cases:**
- "Quando é que o carteiro chegou?"
- "O vizinho do 3º andar passou cá"
- Alerta: "Pessoa à porta há 5 min (possível assalto)"
- Registo de entregas (Amazon, correio)

---

### 8. **Privacy-First Modes**
**Status:** 📋 Planned

**Features:**
- Modo Privacidade (pessoas em casa → menos gravação)
- Zonas privadas (WC, quartos)
- Máscara automática de faces
- Apagar dados automaticamente

**Use Cases:**
- **Modo Família:** Augusto/Sofia em casa → Só alertas de segurança
- **Modo Ausente:** Casa vazia → Gravação total
- **Modo Noite:** 23h-08h → Só deteção de intrusos
- **GDPR Compliance:** Apagar dados > 30 dias

---

### 9. **Voice & Chat Control**
**Status:** ✅ Telegram Active

**Features:**
- Comandos por Telegram
- Consultas naturais
- Alertas proativos
- Resumo por voz

**Use Cases:**
- "Quem está em casa?"
- "Mostra-me a cozinha agora"
- "Fecha os estores da sala"
- "Resumo do dia"

---

### 10. **Predictive Intelligence**
**Status:** 🌙 Future (Moonshot)

**Features:**
- Prever chegadas baseado em padrões
- Deteção precoce de problemas (saúde, segurança)
- Otimização de energia preditiva
- Sugestões de conforto

**Use Cases:**
- "Provavelmente o Augusto chega às 19h, pré-aquecer casa"
- "A Sofia está a dormir mal (análise de padrões)"
- "Prever fuga de água antes de acontecer"
- "Sugerir ligar luzes antes de anoitecer"

---

## 🛠️ Implementation Roadmap

### Fase 1: Foundation ✅ (Concluída)
- ✅ Deteção de pessoas (YOLO)
- ✅ Captura contínua (2s)
- ✅ Alertas Telegram
- ✅ Base de dados de família

### Fase 2: Intelligence 🔄 (Atual)
- 🔄 Face Recognition
- 🔄 Behavioral Baseline
- 🔄 Daily Reports
- 🔄 Anomaly Detection

### Fase 3: Integration 📋 (Próxima)
- 📋 Door Entry/Exit
- 📋 Smart Home (estores, luzes, AC)
- 📋 Activity Heatmap
- 📋 Visitor Log

### Fase 4: Prediction 🌙 (Futuro)
- 🌙 Predictive Analytics
- 🌙 Health Monitoring
- 🌙 Full Home Automation
- 🌙 AI Assistant Integration

---

## 🎯 Prioridades do Utilizador

1. **Privacidade** — Família em casa = menos intrusão
2. **Relevância** — Poucos alertas mas importantes
3. **Automação** — Casa que responde à presença
4. **Simplicidade** — Interface simples, resultados claros

---

*Documento vivo — actualizado conforme novas ideias surgem*
