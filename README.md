# TeachAgent

TeachAgent 是一个 FastAPI + LangGraph + Vue 的教学代理原型。学生输入关键词或粘贴文本后，后端会生成讲解和检测题；学生提交回答后，系统判断掌握情况。如果没有掌握，会指出薄弱点、给出补救说明，并继续出题检测，直到通过。

## 后端

```bash
conda activate langchain
pip install -r requirements.txt
uvicorn main:app --reload
```

接口：

- `POST /api/sessions`：创建学习会话
- `POST /api/sessions/stream`：流式创建学习会话，逐步返回讲解内容
- `POST /api/sessions/{session_id}/answer`：提交回答并触发评估
- `POST /api/sessions/{session_id}/answer/stream`：流式提交回答，逐步返回补救讲解
- `GET /api/sessions/{session_id}`：查看会话

## 前端

```bash
cd frontend
npm install
npm run dev
```

默认前端地址是 `http://127.0.0.1:5173`，后端地址是 `http://127.0.0.1:8000`。

## 一键启动

```bash
./scripts/start.sh
```

默认会启动：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`

停止服务：

```bash
./scripts/stop.sh
```

如果 conda 环境或端口不同：

```bash
CONDA_ENV=langchain BACKEND_PORT=8000 FRONTEND_PORT=5173 ./scripts/start.sh
```

前端目录：

- `src/api`：后端请求封装
- `src/components`：可复用业务组件
- `src/composables`：组合式状态与业务流程
- `src/constants`：页面常量
- `src/pages`：页面级容器
- `src/style.css`：全局视觉系统与响应式布局

后端目录：

- `app/api`：FastAPI 路由层
- `app/core`：应用配置
- `app/services`：会话业务服务
- `app/models.py`：Pydantic 数据模型
- `app/tutor_engine.py`：LangGraph 教学流程
- `app/deepseek_client.py`：DeepSeek OpenAI-compatible 客户端

## 说明

## DeepSeek V4

复制 `.env.example` 为 `.env`，或在 shell 中设置环境变量：

```bash
export DEEPSEEK_API_KEY=sk-your-api-key
export DEEPSEEK_MODEL=deepseek-v4-flash
```

可选模型：

- `deepseek-v4-flash`：默认值，适合先跑通教学交互
- `deepseek-v4-pro`：适合更高质量解释和评估

如果没有配置 `DEEPSEEK_API_KEY`，系统会自动使用本地规则回退。LangGraph 的节点按 `explain -> quiz -> evaluate -> remediate -> quiz` 的循环组织，配置 DeepSeek 后，这些节点会优先调用真实模型。

## 提交到 GitHub

当前项目目录还不是 Git 仓库。建议按下面流程提交：

```bash
git init
git add .
git status
git commit -m "Initial TeachAgent project"
```

然后在 GitHub 创建一个空仓库，不要勾选自动生成 README、`.gitignore` 或 license。创建后执行：

```bash
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

如果你使用 HTTPS 远程地址：

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

注意：`.env` 已被 `.gitignore` 忽略，不会提交 API key。提交前可以用下面命令确认：

```bash
git status --short
git check-ignore -v .env
```
