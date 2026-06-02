# 画廊入口交互系统

本地 iPad 入口接待原型，包含虚拟形象界面、快捷问答、文字交互和管理预览页。

基础资料已按 Moon Gallery & Studio 官网整理，包括主画廊地址、联系方式、展览/销售/工房/艺术学校等服务信息。

## 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 接入语言模型

默认不配置模型时，系统使用本地 FAQ 规则回复。配置下面环境变量后，会优先调用 OpenAI 兼容的聊天接口，失败时自动回退到本地规则。

### DeepSeek

推荐使用本地 `.env` 文件保存 key：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

启动：

```bash
.venv/bin/python app.py
```

也可以用环境变量：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
.venv/bin/python app.py
```

默认使用 `deepseek-chat`。如果想改用推理模型：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
export LLM_MODEL="deepseek-reasoner"
.venv/bin/python app.py
```

当前 DeepSeek 官方 OpenAI 兼容地址为 `https://api.deepseek.com`。

### 通用 OpenAI 兼容接口

```bash
export LLM_API_KEY="你的 API Key"
export LLM_MODEL="模型名称"
export LLM_BASE_URL="https://api.openai.com/v1"
python app.py
```

### OpenAI

如果使用 OpenAI，可只设置 `OPENAI_API_KEY` 和 `LLM_MODEL`：

```bash
export OPENAI_API_KEY="你的 API Key"
export LLM_MODEL="gpt-4.1-mini"
python app.py
```

如果使用其他兼容服务，把 `LLM_BASE_URL` 改成对应服务的接口地址即可。

浏览器访问：

- 接待界面：http://localhost:5002
- 管理页：http://localhost:5002/manage
- 健康检查：http://localhost:5002/health

## 麦克风权限

浏览器通常只允许安全来源使用麦克风。PC 端测试请优先使用：

```text
http://localhost:5002
```

如果浏览器仍然限制麦克风，可以使用本地 HTTPS：

```bash
HTTPS=1 PORT=5443 .venv/bin/python app.py
```

然后访问：

```text
https://localhost:5443
```

第一次打开会看到自签名证书警告，选择继续访问后，再允许麦克风权限。

同一 Wi-Fi 下的 iPad 可访问电脑局域网 IP，例如：

```text
http://你的电脑IP:5002
```

## 云端部署

本项目已准备好云端部署文件：

- `requirements.txt`：包含 Flask 和 gunicorn
- `Procfile`：Heroku/Railway 等平台可用
- `render.yaml`：Render Blueprint 可用
- `runtime.txt`：指定 Python 版本

### Render 推荐步骤

1. 把项目上传到 GitHub 仓库。
2. 在 Render 创建 Web Service，连接该仓库。
3. Build Command:

```bash
pip install -r requirements.txt
```

4. Start Command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60
```

5. 在 Render 的 Environment 里设置：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
LLM_MODEL=deepseek-chat
```

不要上传本地 `.env`、`.venv` 或 `certs`。云端平台会自动提供 HTTPS，语音唤醒要通过云端 HTTPS 地址访问。
