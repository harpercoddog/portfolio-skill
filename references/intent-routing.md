# Intent Routing

当用户消息满足以下模式时，调用对应脚本：

## 1. 记录交易

触发词：

- 买入
- 卖出
- 分红
- 股息
- 转入
- 转出

最低信息要求：

- 标的代码
- 账户名
- 对于买入、卖出、转入，需要价格或成本
- 对于买入、卖出、转入、转出，需要数量
- 对于分红，需要金额

推荐调用：

```bash
python scripts/record_trade.py --text "<用户原始输入>"
```

## 2. 查询持仓

触发词：

- 持仓
- 成本价
- 收益
- 市值
- 组合
- 某个账户现在持有哪些

推荐调用：

```bash
python scripts/query_portfolio.py
python scripts/query_portfolio.py --account "美股账户"
python scripts/query_portfolio.py --symbol "AAPL"
```

## 3. 同步价格

触发词：

- 同步价格
- 更新行情
- 获取最新股价
- 刷新报价

推荐调用：

```bash
python scripts/sync_prices.py --provider mock
```

## 4. 组合分析

触发词：

- 分析组合
- 给我建议
- 看看仓位风险
- 输出分析报告

推荐调用：

```bash
python scripts/analyze_portfolio.py
```

