# Sample Commands

## 自然语言输入示例

- 买入 AAPL 10 股，价格 210，账户是美股账户
- 卖出 510300 100 份，价格 4.25，账户是A股账户
- 分红 AAPL 12.5，账户是美股账户
- 转入 159919 200 份，成本 2.35，账户是A股账户
- 转出 AAPL 2 股，账户是美股账户

## CLI 调用示例

```bash
python scripts/init_db.py --db-path data/portfolio.db
python scripts/record_trade.py --text "买入 AAPL 10 股，价格 210，账户是美股账户" --db-path data/portfolio.db
python scripts/record_trade.py --text "卖出 510300 100 份，价格 4.25，账户是A股账户" --db-path data/portfolio.db
python scripts/sync_prices.py --provider auto --db-path data/portfolio.db
python scripts/query_portfolio.py --db-path data/portfolio.db
python scripts/query_portfolio.py --account "美股账户" --db-path data/portfolio.db
python scripts/query_portfolio.py --symbol AAPL --db-path data/portfolio.db
python scripts/analyze_portfolio.py --db-path data/portfolio.db
```
