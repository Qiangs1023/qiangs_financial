# FinPulse - 金融监控预测系统

金融市场监控与波动预测工具，支持多市场数据采集、政策分析、LLM智能预测。

## 功能特性

- **多市场数据采集**: A股、美股、港股、加密货币
- **政策新闻监控**: RSS订阅、舆情分析
- **LLM智能分析**: 市场情绪、政策影响、波动预测 (DeepSeek)
- **实时预警**: 异动监控、风险提示
- **多渠道通知**: Telegram、企业微信
- **GitHub Actions**: 自动定时运行，无需服务器

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置

```bash
# 复制配置模板
cp .env.example .env
cp config.example.yaml config.yaml

# 编辑 .env 填入 API Keys
```

### 3. 运行

```bash
# 单次分析
finpulse analyze

# 启动监控
finpulse monitor

# 测试通知
finpulse test-notify
```

## GitHub Actions 部署

### 步骤 1: 创建 GitHub 仓库

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/finpulse.git
git push -u origin main
```

### 步骤 2: 配置 Secrets

在 GitHub 仓库页面，进入 **Settings → Secrets and variables → Actions**，添加以下 secrets：

| Secret 名称 | 说明 |
|------------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID |
| `WECHAT_WEBHOOK` | 企业微信 Webhook (可选) |

### 步骤 3: 启用 Actions

1. 进入 **Actions** 标签页
2. 启用 workflow
3. 可手动触发或等待定时任务

### 定时任务说明

- 每小时自动分析并发送通知
- 工作日早8点发送每日晨报

## CLI 命令

| 命令 | 说明 |
|-----|------|
| `finpulse analyze` | 运行一次性分析 |
| `finpulse monitor` | 启动持续监控 |
| `finpulse test-notify` | 测试通知渠道 |
| `finpulse config-check` | 检查配置 |
| `finpulse init` | 初始化配置文件 |

## 获取 API Keys

### DeepSeek
1. 访问 https://platform.deepseek.com
2. 注册并创建 API Key

### Telegram Bot
1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 创建机器人
3. 获取 Bot Token
4. 向 Bot 发送消息后访问获取 Chat ID:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

### 企业微信
1. 在企业微信群中添加机器人
2. 获取 Webhook 地址

## 项目结构

```
finpulse/
├── src/
│   ├── cli.py              # CLI入口
│   ├── config.py           # 配置管理
│   ├── collectors/         # 数据采集
│   ├── analyzer/           # LLM分析引擎
│   ├── scheduler/          # 定时任务
│   └── notifier/           # 通知推送
├── .github/workflows/      # GitHub Actions
├── config.yaml             # 配置文件
└── .env                    # 环境变量
```

## License

MIT
