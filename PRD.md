# PRD — ServerPulse: Dashboard de Métricas de Servidores

> **Instrucciones para el asistente de IA del IDE:**
> Este documento describe el proyecto completo. Léelo de principio a fin antes de empezar.
> Implementa **todo** lo descrito sin pedir confirmaciones intermedias.
> Si una decisión técnica no está especificada, toma la opción más simple y documenta tu elección en el README.
> Al terminar cada fase, ejecuta los tests y comandos de verificación de esa fase antes de pasar a la siguiente.
> Trabaja en commits atómicos por fase con mensajes en formato Conventional Commits.

---

## 1. Visión del producto

**ServerPulse** es una plataforma open-source que permite a un sysadmin monitorear múltiples servidores Linux desde un único panel web. Los servidores monitoreados ejecutan un agente ligero (script Python) que envía métricas a intervalos regulares a una API central, que las almacena y las muestra en un dashboard con gráficos en tiempo real.

**Objetivo del proyecto:** servir como pieza central de un portafolio para un perfil junior de Desarrollador / Sysadmin / DevOps. Cada decisión debe priorizar **claridad, buenas prácticas y demostrabilidad** sobre features avanzadas.

---

## 2. Usuarios y casos de uso

**Usuario único:** un sysadmin que gestiona entre 1 y 20 servidores Linux.

**Casos de uso principales:**
1. Registrar un nuevo servidor y obtener un token de API para su agente.
2. Instalar el agente en el servidor remoto con un comando de una línea.
3. Ver en el dashboard métricas de CPU, RAM, disco, red y uptime de todos sus servidores.
4. Recibir una alerta visual (no email) cuando un servidor lleva más de 2 minutos sin enviar datos.
5. Consultar el histórico de las últimas 24 horas de cada métrica.

---

## 3. Stack técnico (obligatorio)

| Capa | Tecnología | Versión mínima |
|---|---|---|
| Backend API | Python 3.11 + FastAPI | FastAPI 0.110+ |
| Base de datos | PostgreSQL | 16 |
| Cache / pub-sub en tiempo real | Redis | 7 |
| Migraciones | Alembic | última |
| ORM | SQLAlchemy 2.0 (async) | 2.0+ |
| Frontend | React 18 + Vite + TypeScript | — |
| Gráficos | Recharts | última |
| Estilos | TailwindCSS | 3 |
| Agente | Python 3.8+ (compatible con stdlib + `psutil` + `requests`) | — |
| Contenerización | Docker + docker compose v2 | — |
| Reverse proxy | Nginx (en contenedor) | latest stable |
| CI/CD | GitHub Actions | — |
| Tests backend | pytest + pytest-asyncio + httpx | — |
| Tests frontend | Vitest + React Testing Library | — |
| Linter Python | ruff | — |
| Formatter Python | ruff format | — |
| Linter JS/TS | ESLint + Prettier | — |
| Monitoreo del propio stack | Prometheus + Grafana (en docker-compose) | — |

**No uses** otras tecnologías sin documentarlo en el README.

---

## 4. Estructura del repositorio

```
serverpulse/
├── README.md
├── LICENSE                       # MIT
├── .gitignore
├── .env.example
├── docker-compose.yml            # stack de producción
├── docker-compose.dev.yml        # override para desarrollo (hot reload)
├── docker-compose.monitoring.yml # Prometheus + Grafana
├── Makefile                      # atajos: make up, make test, make lint, etc.
├── docs/
│   ├── architecture.md           # diagrama + explicación
│   ├── api.md                    # referencia de endpoints
│   └── deployment.md             # cómo desplegar en un VPS
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # entry point FastAPI
│   │   ├── config.py            # settings con pydantic-settings
│   │   ├── database.py          # engine async + session
│   │   ├── redis_client.py
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/
│   │   │   ├── deps.py          # dependencias (auth, db)
│   │   │   ├── auth.py
│   │   │   ├── servers.py
│   │   │   ├── metrics.py
│   │   │   └── ws.py            # WebSocket para tiempo real
│   │   ├── core/
│   │   │   ├── security.py      # JWT + hashing tokens
│   │   │   └── alerts.py        # lógica de detección de servidores caídos
│   │   └── tasks/
│   │       └── cleanup.py       # purga de métricas > 24h
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_servers.py
│       └── test_metrics.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/                 # cliente HTTP
│       ├── components/
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── ServerDetail.tsx
│       │   └── ServerNew.tsx
│       ├── hooks/
│       └── types/
├── agent/
│   ├── README.md                # instrucciones de instalación
│   ├── serverpulse-agent.py     # script único, autoejecutable
│   ├── serverpulse-agent.service # unit file de systemd
│   ├── install.sh               # instalador one-liner
│   └── requirements.txt
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       └── dashboards/
│           └── serverpulse.json
├── scripts/
│   ├── backup_db.sh
│   └── restore_db.sh
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

---

## 5. Modelo de datos

Crear con Alembic. Todas las tablas con `created_at TIMESTAMPTZ DEFAULT NOW()`.

### `users`
| Columna | Tipo | Notas |
|---|---|---|
| id | UUID PK | gen_random_uuid() |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| password_hash | VARCHAR(255) NOT NULL | bcrypt |
| created_at | TIMESTAMPTZ | |

### `servers`
| Columna | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users.id | ON DELETE CASCADE |
| name | VARCHAR(100) NOT NULL | |
| hostname | VARCHAR(255) | nullable |
| api_token_hash | VARCHAR(255) NOT NULL | hash del token que usa el agente |
| last_seen_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | |

Índice: `(user_id)`, `(api_token_hash)`.

### `metrics`
| Columna | Tipo | Notas |
|---|---|---|
| id | BIGSERIAL PK | |
| server_id | UUID FK → servers.id | ON DELETE CASCADE |
| cpu_percent | REAL NOT NULL | 0-100 |
| ram_percent | REAL NOT NULL | 0-100 |
| ram_used_mb | INTEGER NOT NULL | |
| ram_total_mb | INTEGER NOT NULL | |
| disk_percent | REAL NOT NULL | particion root |
| disk_used_gb | REAL NOT NULL | |
| disk_total_gb | REAL NOT NULL | |
| net_rx_bytes | BIGINT NOT NULL | acumulado desde boot |
| net_tx_bytes | BIGINT NOT NULL | |
| uptime_seconds | BIGINT NOT NULL | |
| load_avg_1 | REAL | |
| load_avg_5 | REAL | |
| load_avg_15 | REAL | |
| recorded_at | TIMESTAMPTZ NOT NULL | timestamp del lado del agente |
| received_at | TIMESTAMPTZ DEFAULT NOW() | timestamp del servidor |

Índice compuesto: `(server_id, recorded_at DESC)`.

**Retención:** un cron interno (task asíncrona cada hora) borra registros con `received_at < NOW() - INTERVAL '24 hours'`.

---

## 6. API REST

Base URL: `/api/v1`. Todas las respuestas en JSON. Errores con esquema `{"detail": "mensaje"}`.

### Autenticación de usuario (panel web)
- `POST /api/v1/auth/register` → `{email, password}` → 201 `{id, email}`
- `POST /api/v1/auth/login` → `{email, password}` → 200 `{access_token, token_type:"bearer"}` (JWT, expiración 24h)
- `GET /api/v1/auth/me` → 200 `{id, email}` (requiere JWT)

### Servidores (requieren JWT)
- `POST /api/v1/servers` → `{name, hostname?}` → 201 `{id, name, hostname, api_token}` (**el token solo se devuelve aquí, una vez**)
- `GET /api/v1/servers` → 200 `[{id, name, hostname, last_seen_at, status}]`  
  `status` se calcula: `online` si `last_seen_at` < 2min, `offline` si > 2min o nunca visto.
- `GET /api/v1/servers/{id}` → 200 detalle + última métrica
- `DELETE /api/v1/servers/{id}` → 204
- `POST /api/v1/servers/{id}/regenerate-token` → 200 `{api_token}`

### Métricas
- `POST /api/v1/metrics/ingest` → **autenticado con header `X-Agent-Token: <token>`** (no JWT). Body con todos los campos de la tabla `metrics` excepto `id`, `server_id`, `received_at`. Responde 202 sin body.
- `GET /api/v1/servers/{id}/metrics?from=<iso>&to=<iso>` → 200 `[{recorded_at, cpu_percent, ...}]` (requiere JWT, máximo 24h, máximo 2880 puntos).

### WebSocket
- `WS /api/v1/ws?token=<jwt>` → emite por Redis pub/sub. Mensajes:
  ```json
  {"type":"metric","server_id":"...","data":{...}}
  {"type":"status_change","server_id":"...","status":"offline"}
  ```

### Health
- `GET /health` → 200 `{"status":"ok","db":"ok","redis":"ok"}` (usado por Docker healthcheck)
- `GET /metrics` → métricas Prometheus (usar `prometheus-fastapi-instrumentator`)

---

## 7. Agente

Archivo único `agent/serverpulse-agent.py` ejecutable. Sin dependencias más allá de `psutil` y `requests`.

**Comportamiento:**
1. Lee config de `/etc/serverpulse/agent.conf` (formato INI) con `api_url` y `api_token`.
2. Cada 15 segundos recolecta métricas con `psutil` y hace `POST` al endpoint de ingesta.
3. Si la petición falla, reintenta con backoff exponencial (máx 5min) sin perder el ciclo de 15s.
4. Loguea a stdout (capturado por systemd journal).
5. Maneja SIGTERM limpiamente.

**`install.sh`:** descarga el script y el service file, crea usuario `serverpulse`, instala dependencias, pide al usuario la URL de la API y el token, escribe la config y habilita el servicio. Debe poder ejecutarse con:

```bash
curl -fsSL https://raw.githubusercontent.com/<user>/serverpulse/main/agent/install.sh | sudo bash -s -- --url https://api.example.com --token abc123
```

---

## 8. Frontend

**Páginas:**

1. **`/login`** y **`/register`** — formularios simples, validación con react-hook-form + zod.
2. **`/`** (Dashboard) — grid de tarjetas, una por servidor. Cada tarjeta muestra:
   - Nombre + hostname
   - Indicador de status (verde/rojo) con animación
   - Gauges/sparklines de CPU y RAM (última hora)
   - Uptime formateado (`5d 3h 22m`)
   - Última actualización (`hace 12s`)
3. **`/servers/new`** — formulario para registrar servidor. Tras crearlo, muestra el token UNA SOLA VEZ con botón de copiar y el comando de instalación del agente listo para copiar.
4. **`/servers/:id`** — detalle: 4 gráficos de líneas (CPU, RAM, disco, red), selector de rango (1h / 6h / 24h), botón para regenerar token y botón para borrar servidor (con confirmación).

**Tiempo real:** un hook `useLiveMetrics()` conecta al WebSocket y actualiza el estado local. Si el WS se cae, fallback a polling cada 15s.

**Diseño:**
- Tema oscuro por defecto (paleta tipo Grafana: fondo `#0e1116`, acentos azul/verde).
- Mobile-friendly (no es la prioridad pero no debe romperse en móvil).
- Sin librerías de componentes pesadas; usar TailwindCSS y, como mucho, `lucide-react` para iconos.

---

## 9. Seguridad

- Passwords con **bcrypt** (12 rounds).
- JWT firmado con HS256, secret de mínimo 32 bytes leído de env `JWT_SECRET`.
- Tokens de agente: generados con `secrets.token_urlsafe(32)`, almacenados solo como hash (sha256 con salt fijo del proyecto, suficiente para este caso de uso — documentar el trade-off en el README).
- CORS configurable por env, por defecto solo el dominio del frontend.
- Rate limiting con `slowapi`: 5 req/min en login y register, 60 req/min por agente en ingest.
- Validación estricta de inputs con Pydantic (rangos: porcentajes 0-100, etc.).
- Headers de seguridad en Nginx: `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`.
- No loguear nunca tokens ni passwords.

---

## 10. Docker y orquestación

### `docker-compose.yml` (producción)
Servicios:
- `postgres:16-alpine` con volumen `pgdata`, healthcheck.
- `redis:7-alpine` con healthcheck.
- `backend` (build desde `./backend`), depende de postgres + redis healthy, ejecuta migraciones de Alembic al arrancar (entrypoint script).
- `frontend` (build con multi-stage: node para build, nginx para servir estáticos).
- `nginx` reverse proxy, puerto 80 y 443, monta certificados de `./certs` (gestionados con certbot fuera de compose).

Todos los servicios en una red `serverpulse_net`. Variables sensibles desde `.env` (con `.env.example` commiteado).

### `docker-compose.dev.yml`
Override: monta el código como volumen, ejecuta `uvicorn --reload` y `vite dev`, expone puertos directamente.

### `docker-compose.monitoring.yml`
Servicios `prometheus` y `grafana`. Prometheus scrapea `/metrics` del backend. Grafana provisiona automáticamente el datasource y un dashboard predefinido.

### Healthchecks
Todos los servicios deben tener healthcheck. El backend solo se considera healthy cuando `/health` responde 200 con db y redis OK.

---

## 11. CI/CD con GitHub Actions

### `.github/workflows/ci.yml` (trigger: push y PR a cualquier rama)
Jobs en paralelo:
1. **backend-lint:** ruff check + ruff format --check.
2. **backend-test:** levanta postgres + redis como services, ejecuta `pytest --cov`, sube coverage como artifact.
3. **frontend-lint:** ESLint + tsc --noEmit.
4. **frontend-test:** vitest run.
5. **docker-build:** build de las imágenes (sin push) para validar Dockerfiles.

### `.github/workflows/deploy.yml` (trigger: push a `main` tras CI verde)
1. Login en GHCR.
2. Build y push de imágenes con tags `latest` y `sha-<short>`.
3. SSH al VPS (usando `appleboy/ssh-action` con secret `DEPLOY_KEY`).
4. En el VPS: `cd /opt/serverpulse && docker compose pull && docker compose up -d && docker image prune -f`.
5. Espera 30s y verifica `curl https://dominio/health`. Si falla, ejecuta rollback (`docker compose up -d` con tag anterior guardado).

Secrets necesarios (documentar en `docs/deployment.md`):  
`DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY`, `GHCR_TOKEN`.

---

## 12. Sysadmin / Operaciones

Documentar en `docs/deployment.md` los siguientes pasos manuales para el VPS:

1. Ubuntu 24.04 LTS limpio.
2. Usuario no-root con sudo, deshabilitar login root y password SSH.
3. `ufw`: permitir 22, 80, 443. Denegar resto.
4. `fail2ban` con jail para sshd.
5. Instalar Docker Engine y Compose plugin.
6. Clonar repo en `/opt/serverpulse`, crear `.env` desde `.env.example`.
7. Obtener certificados con `certbot --nginx` (modo standalone la primera vez, luego renovación con cron y reload de Nginx).
8. `docker compose up -d`.
9. Configurar cron para backup diario: `0 3 * * * /opt/serverpulse/scripts/backup_db.sh`.

### `scripts/backup_db.sh`
Hace `pg_dump` dentro del contenedor de postgres, comprime con gzip, guarda en `/var/backups/serverpulse/` con nombre `serverpulse-YYYYMMDD.sql.gz`, borra backups con más de 14 días.

### `scripts/restore_db.sh`
Recibe el nombre del backup como argumento y lo restaura tras pedir confirmación.

---

## 13. Tests

**Backend (cobertura mínima 70% en `app/`):**
- Auth: registro, login OK, login con password incorrecto, JWT inválido, JWT expirado.
- Servers: CRUD completo, aislamiento entre usuarios (usuario A no puede ver servers de B).
- Metrics ingest: token válido, token inválido, payload inválido, actualización de `last_seen_at`.
- Metrics query: filtrado por rango, límite de puntos.
- Alerts: lógica de detección de offline.

**Frontend (smoke tests):**
- Renderiza Login sin crash.
- Renderiza Dashboard con datos mockeados.
- Hook `useLiveMetrics` se conecta y reconecta tras error.

---

## 14. README.md

Debe incluir, en este orden:
1. Logo/título y badge de build (GitHub Actions).
2. Descripción corta y screenshot del dashboard (placeholder ahora, se añade después).
3. Stack técnico (tabla).
4. Diagrama de arquitectura ASCII o link a `docs/architecture.md`.
5. Quickstart en local: `make up` y abrir `http://localhost`.
6. Cómo añadir un servidor (panel → registrar → copiar one-liner del agente).
7. Sección "Decisiones técnicas" explicando por qué FastAPI vs Flask, por qué Postgres vs InfluxDB, por qué WebSocket vs SSE, etc. (mínimo 5 decisiones).
8. Roadmap futuro (alertas por email, soporte multi-tenant, etc.).
9. Licencia MIT.

---

## 15. Plan de ejecución por fases

Implementa estrictamente en este orden. Al final de cada fase, ejecuta los comandos de verificación y haz commit.

### Fase 0 — Bootstrap
- Crear estructura de carpetas vacías.
- `.gitignore`, `LICENSE`, `README.md` inicial, `Makefile` con targets vacíos.
- `.env.example`.
- **Verificar:** `tree -L 2` muestra la estructura.
- **Commit:** `chore: initial project scaffolding`

### Fase 1 — Backend base
- `pyproject.toml` con dependencias.
- Config con pydantic-settings.
- Conexión async a Postgres y Redis.
- Modelos SQLAlchemy.
- Primera migración de Alembic.
- Endpoint `/health`.
- Dockerfile y entrada en docker-compose.
- **Verificar:** `docker compose up -d postgres redis backend && curl localhost:8000/health` → 200.
- **Commit:** `feat(backend): base setup with db, redis and healthcheck`

### Fase 2 — Auth
- Endpoints register, login, me.
- Dependencia `get_current_user`.
- Tests de auth pasando.
- **Verificar:** `pytest backend/tests/test_auth.py` verde.
- **Commit:** `feat(auth): user registration, login and JWT`

### Fase 3 — Servers CRUD
- Endpoints de servers.
- Generación y hash de tokens de agente.
- Tests.
- **Verificar:** `pytest backend/tests/test_servers.py` verde.
- **Commit:** `feat(servers): CRUD with API tokens`

### Fase 4 — Ingesta de métricas
- Endpoint ingest con auth por token.
- Endpoint de query con rango.
- Task de cleanup.
- Publicación en Redis pub/sub al recibir métrica.
- Tests.
- **Verificar:** `pytest backend/tests/test_metrics.py` verde.
- **Commit:** `feat(metrics): ingestion endpoint and query`

### Fase 5 — WebSocket
- Endpoint WS con auth por query param.
- Suscripción a Redis pub/sub.
- Lógica de detección de offline (task periódica que comprueba `last_seen_at` y publica `status_change`).
- **Verificar:** conectar con `wscat` y recibir mensajes al hacer ingest.
- **Commit:** `feat(ws): realtime updates via websocket`

### Fase 6 — Agente
- Script Python, systemd unit, install.sh.
- Probarlo apuntando al backend en local.
- **Verificar:** ejecutar agente, ver métricas llegando al endpoint y publicadas por WS.
- **Commit:** `feat(agent): metrics collector with systemd integration`

### Fase 7 — Frontend
- Scaffold con Vite + React + TS + Tailwind.
- Páginas Login, Register, Dashboard, ServerNew, ServerDetail.
- Cliente API y hook de WebSocket.
- Tema oscuro.
- **Verificar:** flujo completo manual: registrar usuario → crear server → arrancar agente → ver datos en dashboard.
- **Commit:** `feat(frontend): dashboard with realtime charts`

### Fase 8 — Nginx + producción
- Dockerfile de Nginx con la config.
- docker-compose.yml de producción completo.
- Multi-stage build del frontend.
- **Verificar:** `docker compose up -d` y abrir `http://localhost`.
- **Commit:** `feat(ops): nginx reverse proxy and production compose`

### Fase 9 — CI/CD
- Workflows de GitHub Actions.
- Verificar que el CI pasa en una PR de prueba.
- **Commit:** `ci: github actions for lint, test and deploy`

### Fase 10 — Monitoreo
- docker-compose.monitoring.yml.
- Configuración de Prometheus y dashboard de Grafana.
- **Verificar:** abrir Grafana en `localhost:3001`, ver el dashboard con datos.
- **Commit:** `feat(monitoring): prometheus and grafana stack`

### Fase 11 — Docs y pulido
- Completar README, architecture.md, api.md, deployment.md.
- Hacer screenshots del dashboard y añadirlos.
- Revisar que `make lint` y `make test` pasan en todo el proyecto.
- **Commit:** `docs: complete documentation and screenshots`

---

## 16. Makefile (targets requeridos)

```makefile
make up           # docker compose up -d
make down         # docker compose down
make dev          # up con override dev
make logs         # docker compose logs -f
make test         # pytest + vitest
make lint         # ruff + eslint
make format       # ruff format + prettier
make migrate      # alembic upgrade head
make migration name=...  # alembic revision --autogenerate
make backup       # ejecuta scripts/backup_db.sh
make clean        # docker compose down -v y borra node_modules y __pycache__
```

---

## 17. Criterios de aceptación finales

Antes de considerar el proyecto terminado, verifica que:

- [ ] `make up` levanta el stack completo sin errores en una máquina limpia con solo Docker instalado.
- [ ] Un usuario puede registrarse, crear un servidor y ver sus métricas en el dashboard en menos de 5 minutos.
- [ ] El instalador del agente funciona en una VM Ubuntu 24.04 limpia con un solo comando.
- [ ] Si se apaga un servidor monitoreado, el dashboard lo marca como offline en menos de 3 minutos.
- [ ] Todos los tests pasan en CI.
- [ ] `make lint` no reporta errores.
- [ ] El dashboard de Grafana muestra métricas reales del backend.
- [ ] El README permite a otra persona desplegar el proyecto en su VPS siguiendo solo `docs/deployment.md`.

---

**Fin del PRD. Empieza por la Fase 0.**
