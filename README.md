# Portfolio Skill for OpenClaw / QQ Claw

一个面向聊天式投资记录与组合查询的 MVP skill 项目。它使用 Python + SQLite，围绕四个核心动作实现：

1. `record_trade`
2. `query_portfolio`
3. `sync_prices`
4. `analyze_portfolio`

项目目标是先把最小可用链路打通，方便后续被 OpenClaw / QQ Claw 调用。

## 1. 架构设计

整体设计见 [docs/architecture.md](docs/architecture.md)。

简化版架构如下：

- `scripts/` 暴露四个核心动作的 CLI 入口
- `app/parser.py` 负责自然语言交易解析
- `app/services/transactions.py` 写入交易流水
- `app/services/portfolio.py` 从交易流水推导仓位和收益
- `app/services/pricing.py` 同步最新价格
- `app/services/analytics.py` 输出规则型报告
- `app/providers/` 提供价格源抽象，MVP 默认走 `mock`

## 2. 数据库 Schema

完整 schema 见 [docs/schema.sql](docs/schema.sql)。

核心表：

- `accounts`
- `assets`
- `transactions`
- `price_history`

设计原则：

- 仓位不单独作为唯一真相源
- 由 `transactions` 实时推导当前持仓
- `assets.last_price` 只是当前价格缓存，不替代 `price_history`

## 3. 仓库目录结构

```text
portfolio-skill/
├── SKILL.md
├── README.md
├── requirements.txt
├── .gitignore
├── app/
│   ├── db.py
│   ├── models.py
│   ├── parser.py
│   ├── providers/
│   ├── services/
│   └── utils/
├── docs/
│   ├── architecture.md
│   └── schema.sql
├── scripts/
│   ├── init_db.py
│   ├── record_trade.py
│   ├── query_portfolio.py
│   ├── sync_prices.py
│   └── analyze_portfolio.py
├── references/
│   ├── intent-routing.md
│   └── rules.md
├── data/
│   └── .gitkeep
└── examples/
    └── sample_commands.md
```

## 4. 快速开始

### 环境

- Python 3.9+
- MVP 默认无第三方依赖

### 初始化数据库

```bash
python scripts/init_db.py
```

### 记录交易

```bash
python scripts/record_trade.py --text "买入 AAPL 10 股，价格 210，账户是美股账户"
python scripts/record_trade.py --text "卖出 510300 100 份，价格 4.25，账户是A股账户"
python scripts/record_trade.py --text "分红 AAPL 12.5，账户是美股账户"
python scripts/record_trade.py --text "转入 159919 200 份，成本 2.35，账户是A股账户"
```

### 查询持仓

```bash
python scripts/query_portfolio.py
python scripts/query_portfolio.py --account "美股账户"
python scripts/query_portfolio.py --symbol AAPL
```

输出字段包括：

- 当前数量
- 平均成本
- 最新价格
- 当前市值
- 浮盈浮亏
- 收益率

### 同步价格

```bash
python scripts/sync_prices.py --provider mock
```

已实现的 provider abstraction：

- `get_latest_price(symbol, market, currency)`
- `get_latest_prices(assets)`

当前支持：

- `mock`

预留：

- `YahooFinanceProvider`
- `AkShareProvider`

### 组合分析

```bash
python scripts/analyze_portfolio.py
```

报告至少包含：

- 总市值
- 总浮盈浮亏
- 各账户分布
- 前五大持仓
- 当日波动较大的标的
- 规则型提醒

## 5. 加权平均成本法说明

### 买入

- 更新持仓数量
- 更新总成本
- 重新计算平均成本

### 卖出

- 已实现收益 = 卖出金额 - 手续费 - 平均成本 × 卖出数量
- 剩余持仓继续沿用卖出前平均成本

### 当前市值

- 当前市值 = 当前数量 × 最新价格

### 未实现收益

- 未实现收益 = (最新价格 - 平均成本) × 当前数量

## 6. 规则型建议逻辑

默认规则见 [references/rules.md](references/rules.md)：

- 单日跌幅超过阈值，提醒复盘
- 单一标的仓位过于集中，提醒关注集中度
- 单标的浮盈浮亏超过阈值，提醒检查纪律
- 缺少最新价格，提醒先同步行情

## 7. 适配 OpenClaw / QQ Claw

`SKILL.md` 已定义：

- skill 用途
- 触发场景
- 意图识别方式
- 输出格式
- 对应脚本调用方法

因此它既可以作为独立 GitHub 项目，也可以作为 Skill 根目录直接接入。

## 8. MVP 边界

当前版本刻意保持简单：

- 不处理现金账户
- 不处理多币种汇率换算
- 不处理复杂 corporate action
- 不做 LLM 自由分析，只做规则型提醒

这能保证 `record_trade`、`query_portfolio`、`sync_prices`、`analyze_portfolio` 四个核心动作先稳定可用。
