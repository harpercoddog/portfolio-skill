---
name: portfolio-investment-assistant
description: Use this skill when the user wants to record investment trades in natural language, query current holdings and weighted average cost, sync the latest security prices into a local SQLite database, or generate a rule-based portfolio analysis report for A-share, US, or HK accounts with Python scripts.
---

# 投资助手 Skill

## 用途

这是一个适用于 OpenClaw / QQ Claw 的本地投资助手 skill，用来管理证券交易流水、查询持仓、同步最新价格，并输出规则型组合分析。

## 本地数据读写位置

默认所有数据都读写到本地 SQLite 文件：

```text
data/portfolio.db
```

数据库里会保存：

- `accounts`
- `assets`
- `transactions`
- `price_history`

如果需要改路径，可以使用：

- 环境变量 `PORTFOLIO_DB_PATH`
- 脚本参数 `--db-path /absolute/or/relative/path.db`

## 什么时候调用

当用户提出以下任一类需求时调用本 skill：

- 记录交易：买入、卖出、分红、转入、转出
- 查询持仓：查看当前数量、平均成本、收益、市值
- 同步价格：获取最新股价并更新本地数据库
- 组合分析：输出总览、前五大持仓、波动标的和规则提醒

如果只是一般金融常识问答，而不是操作本地组合数据，不要调用这个 skill。

## 如何识别用户意图

参考 [references/intent-routing.md](references/intent-routing.md)。

### 1. record_trade

当用户消息里出现下列动作词，并且包含标的、数量或金额、账户等信息时，视为记录交易：

- 买入
- 卖出
- 分红 / 股息
- 转入
- 转出

调用：

```bash
python scripts/record_trade.py --text "<用户原始输入>"
python scripts/record_trade.py --text "<用户原始输入>" --db-path data/portfolio.db
```

如用户明确给出交易日期，可追加：

```bash
python scripts/record_trade.py --text "<用户原始输入>" --trade-date YYYY-MM-DD
```

### 2. query_portfolio

当用户想看整体持仓、某个账户持仓、某个标的成本价、收益或市值时调用。

调用：

```bash
python scripts/query_portfolio.py
python scripts/query_portfolio.py --account "美股账户"
python scripts/query_portfolio.py --symbol "AAPL"
python scripts/query_portfolio.py --db-path data/portfolio.db
```

### 3. sync_prices

当用户要求刷新报价、同步行情、获取最新股价时调用。

调用：

```bash
python scripts/sync_prices.py --provider auto
python scripts/sync_prices.py --provider yahoo
python scripts/sync_prices.py --provider akshare
```

默认使用 `auto` provider：

- `CN` 标的优先走 `akshare`
- `US` / `HK` 标的优先走 `yfinance`
- 如需离线演示，可显式使用 `mock`
- 单个标的同步失败时，不应中断整批同步；应把失败原因原样返回

### 4. analyze_portfolio

当用户要求“分析组合”“给我建议”“看看风险”时调用。

调用：

```bash
python scripts/analyze_portfolio.py
python scripts/analyze_portfolio.py --db-path data/portfolio.db
```

提醒逻辑参考 [references/rules.md](references/rules.md)。

## 输出格式

输出应保持简洁、结构化、可直接贴回聊天窗口：

- 记录交易：返回交易类型、账户、标的、数量、价格、金额
- 查询持仓：先给总览，再给逐项持仓
- 多币种组合汇总时，统一按 `CNY` 汇总
- 同步价格：列出同步了哪些标的、使用了哪个价格源
- 所有脚本都应在输出里明确显示当前读写的数据库路径
- 分析组合：至少包含总市值、总浮盈浮亏、账户分布、前五大持仓、当日波动较大的标的、规则提醒

## 调用约定

1. 执行脚本前，默认在 skill 根目录运行
2. 脚本会自动初始化 SQLite 数据库，无需单独建库
3. 默认数据库路径是 `data/portfolio.db`
4. 如果用户要求把持仓数据放到特定本地路径，优先使用 `--db-path`
5. 不要自由编造价格或建议
6. 如果缺少最新价格，应明确提示先执行 `sync_prices`
7. 对于 `转入`，建议要求用户提供价格或成本；对于 `转出`，若未给价格，MVP 允许记录数量变动
