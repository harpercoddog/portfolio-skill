# 投资助手 Skill MVP 架构设计

## 1. 目标

本项目是一个适用于 OpenClaw / QQ Claw 的本地投资助手 skill，围绕四个核心动作构建：

1. `record_trade`：用自然语言记录买入、卖出、分红、转入、转出
2. `query_portfolio`：查询总持仓、账户持仓、单标的持仓
3. `sync_prices`：同步活跃标的的最新价格到 SQLite
4. `analyze_portfolio`：基于规则生成组合分析报告

## 2. MVP 原则

- 只做本地单机版
- 只用 Python 标准库 + SQLite
- 仓位完全由 `transactions` 推导，不把 `positions` 当成唯一真相源
- 价格源先做 provider abstraction，默认接 `auto`
- 建议逻辑先做规则型，不让模型自由发挥

## 3. 模块划分

### `app/db.py`

- 创建 SQLite 连接
- 自动执行 schema 初始化

### `app/parser.py`

- 解析自然语言交易文本
- 识别交易类型、标的、数量、价格、账户、手续费
- 推断市场、币种、资产类型

### `app/services/transactions.py`

- 负责账户和标的的 upsert
- 写入 `transactions`

### `app/services/portfolio.py`

- 从交易流水推导当前仓位
- 使用加权平均成本法计算平均成本、已实现收益、未实现收益
- 支持总览、按账户、按标的过滤

### `app/services/pricing.py`

- 加载活跃标的
- 调用价格 provider
- 写入 `price_history`
- 更新 `assets.last_price`
- `auto` 模式下按市场路由真实数据源

### `app/services/analytics.py`

- 汇总组合市值与盈亏
- 计算账户分布、前五大持仓、日内大波动标的
- 生成规则型提醒

### `app/providers/*`

- `base.py`：统一接口
- `mock_provider.py`：离线演示价格源
- `yahoo_provider.py`：美股 / 港股真实价格源
- `akshare_provider.py`：A 股 / ETF 真实价格源
- `auto_provider.py`：按市场自动路由

## 4. 成本与收益规则

### 买入

- 增加数量
- 新总成本 = 旧总成本 + 买入金额 + 手续费
- 新平均成本 = 新总成本 / 新数量

### 卖出

- 减少数量
- 已实现收益 = 卖出金额 - 手续费 - 平均成本 × 卖出数量
- 剩余持仓继续沿用卖出前平均成本

### 分红

- 不改变数量
- 已实现收益 += 分红金额 - 手续费

### 转入

- 视为外部持仓转入当前账户
- 增加数量
- 需要提供价格或成本，用于补入成本基础

### 转出

- 视为持仓转出当前账户
- 减少数量
- 默认不把转出视为卖出盈利事件
- 手续费计入已实现损益

## 5. 数据流

1. 聊天意图识别后选择脚本
2. 脚本初始化数据库
3. 若是记录交易，则解析文本并写入交易表
4. 若是查询或分析，则由交易流水实时推导仓位
5. 若是同步价格，则写入价格历史并更新资产当前价
6. 分析模块只消费已同步的最新价格和交易推导出的仓位

## 6. 后续可扩展项

- 接入真实 Yahoo Finance / AkShare provider
- 加入多币种汇率换算
- 增加现金流水与资金账户
- 增加测试集和更多自然语言表达式
