# Fase 1 Implementation Roadmap
## Opção B: Scene Understanding + Behavioral Baseline + Semantic Search

**Features selecionadas:**
1. **Feature 1:** Context-Aware Scene Understanding with Local LLM
2. **Feature 2:** Behavioral Baseline & Anomaly Detection
3. **Feature 6:** Semantic Activity Timeline & Natural Language Search

**Duração estimada:** 10-12 semanas
**Início:** 2026-02-13

---

## Arquitetura de Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    VIGILHOME SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│  CAMERAS (Eufy RTSP)                                        │
│  ├── sala (192.168.86.23)                                   │
│  ├── cozinha (192.168.86.51)                                │
│  └── exterior (pending)                                     │
├─────────────────────────────────────────────────────────────┤
│  INFERENCE ENGINE (Mac Mini M4 / Jetson)                    │
│  ├── YOLOv11 (object detection)                             │
│  ├── MiniCPM-V / LLaVA (scene understanding)                │
│  └── Custom models (anomaly detection)                      │
├─────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                 │
│  ├── Vector DB (Chroma) - semantic embeddings               │
│  ├── Time-series DB (TimescaleDB) - behavioral patterns     │
│  └── Object Store (disco1tb) - video/images                 │
├─────────────────────────────────────────────────────────────┤
│  API & SERVICES                                             │
│  ├── Frigate NVR (base)                                     │
│  ├── FastAPI (custom endpoints)                             │
│  └── Telegram Bot (alerts & queries)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Sprint Planning

### Sprint 0: Foundation (Semanas 1-2)
**Objetivo:** Infraestrutura base operacional

**Tarefas:**
- [ ] Instalar Frigate NVR com Docker
- [ ] Configurar YOLOv11 para deteção de objetos/pessoas
- [ ] Setup ChromaDB (vector database)
- [ ] Setup TimescaleDB (time-series)
- [ ] Pipeline de ingestão de frames
- [ ] API base em FastAPI

**Entregável:** Sistema base com deteção de pessoas em tempo real

---

### Sprint 1: Behavioral Data Collection (Semanas 3-4)
**Feature 2 - Parte 1/3**

**Objetivo:** Coletar dados baseline

**Tarefas:**
- [ ] Implementar tracking de pessoas (DeepSORT)
- [ ] Extrair features comportamentais:
  - Horários de entrada/saída
  - Tempo em cada cômodo
  - Frequência de movimento
  - Padrões diários/semanais
- [ ] Armazenar em time-series DB
- [ ] Dashboard de visualização de padrões

**Entregável:** 2 semanas de dados comportamentais coletados

---

### Sprint 2: Scene Understanding MVP (Semanas 5-6)
**Feature 1 - Parte 1/3**

**Objetivo:** Primeira versão de descrição em linguagem natural

**Tarefas:**
- [ ] Deploy MiniCPM-V 2.6 (quantized 4-bit) no Mac Mini
- [ ] Pipeline: Frame → VLM → Descrição textual
- [ ] Prompt engineering para cenários domésticos
- [ ] Cache de embeddings para frames similares
- [ ] Integração com Telegram: enviar descrição + imagem

**Entregável:** Descrições automáticas de eventos no Telegram

---

### Sprint 3: Semantic Search Foundation (Semanas 7-8)
**Feature 6 - Parte 1/2**

**Objetivo:** Base de pesquisa semântica

**Tarefas:**
- [ ] Indexar descrições VLM no ChromaDB
  - Embedding: sentence-transformers/all-MiniLM-L6-v2
  - Metadata: timestamp, câmara, confiança
- [ ] API de search: query → resultados temporais
- [ ] Interface Telegram: comando /search
- [ ] Daily summary automático

**Entregável:** Pesquisa básica funcional via Telegram

---

### Sprint 4: Behavioral Anomaly Detection (Semanas 9-10)
**Feature 2 - Parte 2/3**

**Objetivo:** Detetar anomalias comportamentais

**Tarefas:**
- [ ] Treinar autoencoder em dados coletados
- [ ] Definir threshold de anomalia (percentil 95)
- [ ] Tipos de anomalias:
  - Ausência inesperada (ex: não chegou à hora habitual)
  - Presença estranha (ex: movimento às 3h)
  - Padrão alterado (ex: muito tempo no WC)
- [ ] Alertas no Telegram com contexto

**Entregável:** Alertas de anomalias comportamentais

---

### Sprint 5: Advanced Scene Understanding (Semanas 11-12)
**Feature 1 - Parte 2/3**

**Objetivo:** Descrições ricas e contextuais

**Tarefas:**
- [ ] Fine-tuning do VLM para cenários específicos:
  - Entregas (caixas, uniformes)
  - Animais (cão, gato)
  - Atividades (cozinhar, TV, leitura)
- [ ] Deteção de objetos específicos (YOLO custom)
- [ ] Fusão: deteção + VLM para descrições precisas
- [ ] Identificação de familiares (básico)

**Entregável:** Descrições detalhadas com contexto

---

### Sprint 6: Semantic Search Advanced (Semanas 13-14)
**Feature 6 - Parte 2/2**

**Objetivo:** Pesquisa natural completa

**Tarefas:**
- [ ] NLU layer (spaCy/LLM pequeno) para parsing de queries
- [ ] Filtros temporais: "ontem", "terça", "última semana"
- [ ] Filtros de câmara: "na sala", "na cozinha"
- [ ] Agregações: "quantas visitas", "quanto tempo"
- [ ] Visualização de timeline

**Entregável:** Queries complexas funcionando

---

### Sprint 7: Integration & Polish (Semanas 15-16)
**Features 1, 2, 6 - Parte 3/3**

**Objetivo:** Integração e otimização

**Tarefas:**
- [ ] Cross-feature intelligence:
  - Anomalias → descrição enriquecida
  - Search → anomalias relacionadas
- [ ] Performance optimization:
  - Batch processing para VLM
  - Cache inteligente
- [ ] Onboarding flow:
  - "Aprender casa" (2 semanas de baseline)
  - Configuração de familiares
- [ ] Documentação técnica

**Entregável:** Sistema integrado e documentado

---

## Stack Tecnológico Detalhado

### Core
| Componente | Tecnologia | Versão |
|------------|------------|--------|
| NVR Base | Frigate | 0.14+ |
| Object Detection | YOLOv11 | ONNX quantized |
| VLM | MiniCPM-V 2.6 | INT4 quantized |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 |
| API | FastAPI | 0.100+ |
| Vector DB | Chroma | 0.4+ |
| Time-series | TimescaleDB | 2.12+ |
| Message Queue | Redis | 7+ |

### ML/AI
| Componente | Tecnologia |
|------------|------------|
| Inference | ONNX Runtime / llama.cpp |
| Tracking | DeepSORT |
| Anomaly Detection | PyTorch (autoencoder) |
| NLU | spaCy 3.x |

### Infra
| Componente | Tecnologia |
|------------|------------|
| Container | Docker + Docker Compose |
| Storage | disco1tb (local) |
| Monitoring | Prometheus + Grafana |
| Logs | Loki |

---

## Métricas de Sucesso

### Feature 1: Scene Understanding
- [ ] Descrição gerada em < 2 segundos
- [ ] Precisão > 80% em objetivos identificados
- [ ] Latência total < 5s do evento ao alerta

### Feature 2: Behavioral Baseline
- [ ] 2+ semanas de dados para baseline
- [ ] False positive rate < 10%
- [ ] Deteção de anomalia em < 1 hora do evento

### Feature 6: Semantic Search
- [ ] Query response < 1 segundo
- [ ] Top-3 accuracy > 70%
- [ ] Suporte a 20+ tipos de queries

---

## Riscos & Mitigação

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| Hardware insuficiente | Médio | Alto | Testar com Coral TPU ou cloud híbrido |
| VLM muito lento | Médio | Médio | Processar só frames-chave, não contínuo |
| Falsos positivos elevados | Alto | Médio | Thresholds ajustáveis, feedback loop |
| Privacidade (GDPR) | Baixo | Alto | Tudo local, anonimização opcional |

---

## Orçamento de Recursos

### Hardware (existente)
- Mac Mini M4: ✅ (16GB RAM, Neural Engine)
- disco1tb: ✅
- Câmaras Eufy: ✅ (2/3)

### Software
- Total: €0 (open source)

### Tempo de Desenvolvimento
- Henry (AI Lead): ~80h
- Augusto (testes): ~20h
- Total: ~100h ao longo de 16 semanas

---

##