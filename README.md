# InsightFlow

React/FastAPI 运营分析原型，提供订单、客户、商品、CSV 导入、指标与导出页面，以及可配置的模型问答。演示种子数据用于浏览完整流程。

![InsightFlow](docs/assets/readme-hero.png)

## 本地启动

安装 Docker 和 Compose，从仓库根目录执行：

```bash
docker compose up --build
```

另开终端生成演示数据：

```bash
docker compose exec backend python -m app.utils.seed_data
```

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:5173 |
| 后端 | http://localhost:8000 |
| 接口文档 | http://localhost:8000/docs |

种子账号包括 `admin@insightflow.com`、`manager@insightflow.com` 和 `staff1@insightflow.com`，密码均为 `password123`。种子记录是合成的经营数据，不能代表企业实施成果。

Compose 中的数据库和登录配置适合本地开发。根目录 `.env` 不会自动把所有设置传入容器。模型 Key 和模型名可填写到 `backend/.env`（后端挂载目录中的配置），或在 backend 服务的 `environment` / `env_file` 中显式提供。

## 开发与结构

| 路径 | 用途 |
| --- | --- |
| `backend/app/models/` / `schemas/` | SQLAlchemy 数据模型和 HTTP Schema |
| `backend/app/routers/` | 认证、业务操作、分析、导出与模型接口 |
| `backend/app/services/` | 业务计算与模型调用 |
| `backend/app/utils/` | 种子数据、CSV 和审计工具 |
| `backend/tests/` | 现有认证回归 |
| `frontend/src/` | 页面、API client、组件和状态 |

后端本地开发需要 Python 3.12+ 与 PostgreSQL。将 `backend/.env.example` 复制为 `backend/.env` 并填写数据库设置，从 backend 目录安装依赖和启动：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
python -m pytest tests -q
```

前端从 frontend 目录运行：

```bash
npm ci
npm run dev
npm run build
```

## 模型与实现范围

`backend/app/config.py` 读取 `OPENAI_API_KEY` 和 `OPENAI_MODEL`。模型问答将数据库聚合指标交给配置的服务；提示词要求有据回答，但不是确定性的事实校验或完整经营权限审计。需要真实 Key 才能验证这条外部链路。

启动时通过 `Base.metadata.create_all` 建表。当前不包含版本化数据库迁移、完整业务测试、生产部署验收或指标效果基准。Docker 配置、页面和样例数据表示已有实现范围，不能证明生产就绪。
