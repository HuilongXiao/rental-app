# Rental App

水上器材租赁管理系统。当前仓库包含 V1 需求文档和最小可运行项目骨架。

## 当前状态

目前只包含：

- FastAPI Backend 基础服务；
- React + Vite + TypeScript Frontend 基础页面；
- SQLite 持久化目录；
- Docker Compose；
- Nginx 反向代理配置；
- 环境变量示例。

业务功能、数据库 models、认证和 migration 尚未实现。

## 运行方式

```bash
docker compose up --build
```

打开：`http://localhost:8080`

Backend health check：`http://localhost:8080/api/health`

停止服务：

```bash
docker compose down
```

数据库文件会保存在 `data/` 目录，备份文件会保存在 `backups/` 目录。不要将真实密码、密钥或 `.env` 提交到 Git。

## 文档

详细需求位于 `docs/`：

- `BUSINESS_RULES.md`
- `PRD.md`
- `ER_MODEL.md`
- `ARCHITECTURE.md`
- `V1_FINAL_SPEC.md`

实现必须遵守 `BUSINESS_RULES.md` 和 `V1_FINAL_SPEC.md`。
