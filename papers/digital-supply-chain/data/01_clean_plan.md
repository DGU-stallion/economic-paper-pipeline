# 数据清洗方案

> 项目：digital-supply-chain  
> 生成时间：2026-05-16

---

## 清洗步骤

| 步骤 | 操作 | 变量 | 参数 |
|------|------|------|------|
| S1 | 导入 Excel → Stata (.dta) | 全部 | — |
| S2 | 重命名变量为英文 | 全部 | 见映射表 |
| S3 | Winsorize 1% 缩尾 | Y, Med1, Profit | p=0.01 |
| S4 | 面板设定 xtset | id + year | — |
| S5 | 生成行业/年份虚拟变量 | 待定 | — |
| S6 | 导出清洗后 .dta | 全部 | `data/clean/panel_clean.dta` |

## 变量名映射

| 中文原名 | 英文变量名 | 标签 |
|----------|-----------|------|
| 证券代码 | stkcd | Stock Code |
| 统计年度 | year | Year |
| 供应链韧性 | scr | Supply Chain Resilience |
| 数字化转型指数 | dt | Digital Transformation Index |
| 流程优化度 | process | Process Optimization |
| 企业创新能力 | innov | Innovation Capability |
| 信息共享水平 | info_share | Information Sharing Level |
| 财务杠杆 | lev | Financial Leverage |
| 独董比例 | indep | Independent Director Ratio |
| 企业规模 | size | Firm Size (ln) |
| 企业年龄 | age | Firm Age (ln) |
| 盈利能力 | roa | Profitability (ROA) |
