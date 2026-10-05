# One-Command Setup with Docker Compose

[`compose.yaml`](../compose.yaml) describes the whole SQL Server environment as code: the server, its settings, its storage, and the job that builds the warehouse. Any Mac with Docker Desktop gets the identical setup with one command, and the build waits on its own until SQL Server is ready.

```
docker compose up -d
   │
   ├─ sqlserver  starts SQL Server 2022, healthcheck polls until it answers a query
   │                 │ healthy
   └─ build      ◄───┘ runs sqlserver/build_all.sql (load → dw → rpt → validate), then exits
```

This replaces Steps 3–4 of [`sql_server_local_setup.md`](sql_server_local_setup.md). The Tableau steps there are unchanged.

---

## 1. Prerequisites

- **Docker Desktop**, running, with **4 GB+ memory** (Settings → Resources).
  - On a company-managed Mac, install it through IT's approved software channel and sign in with the account your organization uses.
  - On Apple Silicon, SQL Server runs through Rosetta emulation. It's on by default in current Docker Desktop; check **Settings → General → Use Rosetta for x86_64/amd64 emulation**.
- **git.** Check with `git --version`. If macOS offers to install the Command Line Tools, accept.

Check Docker:

```bash
docker info --format '{{.ServerVersion}} {{.OSType}}/{{.Architecture}}'
```

Expected: a version followed by `linux/x86_64` (Intel) or `linux/aarch64` (Apple Silicon).

## 2. Get the repo

```bash
mkdir -p ~/Documents/GitHub && cd ~/Documents/GitHub
git clone https://github.com/thialp/people-analytics-warehouse.git
cd people-analytics-warehouse
```

Already cloned? Update it instead:

```bash
cd ~/Documents/GitHub/people-analytics-warehouse && git pull
```

Expected: `compose.yaml` and `.env.example` are now in the folder (`ls -a`).

## 3. Set your password

```bash
cp .env.example .env
open -e .env
```

Replace `Change#Me2026` with your own password (8+ characters with upper case, lower case, a number and a symbol), keep the single quotes, and save. `.env` is git-ignored, so the password never reaches GitHub.

## 4. Start everything

If this Mac already has a container named `arcadia-sql` from the manual `docker run` setup, remove it first (its data is rebuilt in this step):

```bash
docker rm -f arcadia-sql
```

Then:

```bash
docker compose up -d
```

Expected (the first run downloads about 1.5 GB):

```
 ✔ Network arcadia_default      Created
 ✔ Volume "arcadia_sqldata"     Created
 ✔ Container arcadia-sql        Healthy
 ✔ Container arcadia-build      Started
```

`Healthy` appears only once SQL Server answers a real query, typically after 20–40 seconds on Intel and 1–2 minutes under Rosetta.

## 5. Watch the build and check it

```bash
docker compose logs -f build
```

Press `Ctrl+C` once you see the validation section. It should show six **PASS** rows, `0` missing rows, and:

```
2022-06-30   11000   10883.10   1126993109.33   1151151241.43
2026-06-30   13189   12928.00   1566743212.90   1551634565.71
```

Then confirm the build job finished cleanly:

```bash
docker compose ps -a
```

Expected: `arcadia-sql` shows `Up … (healthy)` and `arcadia-build` shows `Exited (0)`. Exit code 0 means success. If it shows `Exited (1)`, the logs above say which script failed.

## 6. Connect Tableau

Same as before: [`sql_server_local_setup.md`](sql_server_local_setup.md), Steps 6–9.

**Native connector (try this first):** **Connect → To a Server → Microsoft SQL Server**

| Field | Value |
|---|---|
| Server | `localhost` |
| Database | `ArcadiaHR` |
| Authentication | Username and password |
| Username | `sa` |
| Password | the one in `.env` |
| Require SSL | unchecked |

- **If Tableau says a driver is missing,** use the JDBC route from the setup guide instead. It needs no admin rights, because the driver is a single file in your home folder.
- **If you get a certificate error,** copy [`tableau/sqlserver_trust_local_certificate.tdc`](../tableau/sqlserver_trust_local_certificate.tdc) into `~/Documents/My Tableau Repository/Datasources/` and restart Tableau.

---

## Everyday commands

Run these from the repo folder.

| Command | What it does |
|---|---|
| `docker compose up -d` | Start, and rebuild the warehouse from the CSVs. Run it after `git pull`. |
| `docker compose ps -a` | Status of both containers |
| `docker compose logs build` | The last build and validation output |
| `docker compose stop` | Stop SQL Server. Data is kept. |
| `docker compose down` | Remove the containers. Data is kept in the volume. |
| `docker compose down -v` | Remove containers **and** the data volume. Next `up` starts from zero. |

`restart: unless-stopped` brings SQL Server back whenever Docker Desktop starts, without rebuilding. You only rebuild when you run `up` yourself.

---

## Things worth knowing

### 1. Query the database from Terminal without typing the password

The password already lives inside the container as an environment variable. Add this function to your shell profile once:

```bash
cat >> ~/.zshrc <<'EOF'

# Query the local Arcadia SQL Server: `asql` for a prompt, `asql -Q "SELECT ..."` for one query
asql() { docker exec -it arcadia-sql bash -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -d ArcadiaHR -W -s "|" "$@"' _ "$@"; }
EOF
source ~/.zshrc
```

Try it:

```bash
asql -Q "SELECT function_name, SUM(headcount) AS headcount, FORMAT(SUM(loaded_usd_nominal),'N0') AS loaded_usd FROM rpt.vw_workforce_cost_snapshot WHERE month_end_date = '2026-06-30' GROUP BY function_name ORDER BY SUM(loaded_usd_nominal) DESC"
```

Expected:

```
function_name|headcount|loaded_usd
-------------|---------|----------
Technology|5411|607,109,359
Commercial|3085|379,742,839
Operations|1993|207,038,509
Corporate|1483|202,463,313
Product|749|102,893,724
Marketing|468|67,495,469

(6 rows affected)
```

Just `asql` opens an interactive prompt. Type a query, then `GO` on its own line to run it, and `exit` to leave.

### 2. See the SQL Tableau actually sends

On a corporate warehouse you usually only have read access. Here you are the database administrator, so you can look at the server's own statistics. Refresh an extract or click around a live sheet in Tableau, then run:

```bash
asql -Q "SELECT TOP 5 qs.execution_count AS runs, qs.total_elapsed_time / 1000 AS total_ms, qs.total_logical_reads AS page_reads, LEFT(REPLACE(REPLACE(st.text, CHAR(13), ' '), CHAR(10), ' '), 150) AS query_start FROM sys.dm_exec_query_stats AS qs CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) AS st WHERE st.text NOT LIKE '%dm_exec_query_stats%' ORDER BY qs.total_elapsed_time DESC"
```

You'll see your Custom SQL wrapped inside a subquery Tableau names `Custom SQL Query`, plus every query Tableau generated on top of it and how long each took. This is the starting point for any query-performance work: find what's slow, then find out why.

### 3. Watch the engine work

```bash
docker stats arcadia-sql
```

This is a live view of CPU, memory and disk for SQL Server. Leave it open while Tableau builds an extract and watch the spike, then press `Ctrl+C`. It's useful for judging whether a query is CPU-bound or reading too much.

### 4. Break things safely

Experiment freely: drop tables, rewrite views, try indexes. When you're done, get a fresh copy in a few minutes:

```bash
docker compose down -v && docker compose up -d
```

The difference between `down` and `down -v` is the difference between a container and a volume: the container is the running program, and the volume is the data. Containers are disposable. Volumes are kept until you delete them on purpose.

### 5. Containers talk to each other by name

In `compose.yaml`, the build job connects to `-S sqlserver`, the service name, not `localhost`. Compose puts both containers on a private network with built-in name lookup. From your Mac (and Tableau) the same server is `localhost:1433`, because of the `ports:` mapping. Two views of one server is how most multi-service applications are wired.

### 6. The Docker Desktop app is a dashboard

- **Containers:** start, stop, logs, and a terminal inside `arcadia-sql` (the **Exec** tab).
- **Volumes:** browse `arcadia_sqldata` and see the actual `.mdf` and `.ldf` database files.
- **Images:** see what's downloaded and how much space it uses.

---

## Troubleshooting

| Message | Cause | Fix |
|---|---|---|
| `required variable MSSQL_SA_PASSWORD is missing` | No `.env` file | Step 3 |
| `registry access to mcr.microsoft.com is not allowed` | Your organization's Docker settings block Microsoft's image registry | Ask IT to allow `mcr.microsoft.com` |
| `x509: certificate signed by unknown authority` | A corporate network inspects encrypted traffic | Try off VPN, or ask IT for Docker's proxy settings |
| `Bind for 0.0.0.0:1433 failed: port is already allocated` | Something else uses port 1433, such as an old `arcadia-sql` | `docker rm -f arcadia-sql`, or change `"1433:1433"` to `"14333:1433"` and use `localhost, 14333` in Tableau |
| `arcadia-sql` stays `unhealthy` | Usually a password that breaks SQL Server's rules | `docker compose logs sqlserver`, fix `.env`, then `docker compose down -v && docker compose up -d` |
| `arcadia-build` shows `Exited (1)` | A build script failed | `docker compose logs build` shows which one |
