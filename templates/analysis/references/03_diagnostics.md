# 诊断检验决策表

## 检验命令

```stata
* 基准模型
reg y x1 x2 x3
predict resid, resid

* 4a. 残差正态性
swilk resid           // Shapiro–Wilk (N ≤ 5000)
sktest resid          // 偏度+峰度检验

* 4b. 异方差检验
estat hettest         // Breusch–Pagan / Cook–Weisberg
estat imtest, white   // White 检验

* 4c. 面板自相关
xtset id year
xtreg y x1 x2, fe
xtserial y x1 x2     // Wooldridge 自相关检验
xttest3               // 修正 Wald 组间异方差

* 4d. 横截面相关
xtcsd, pesaran abs    // Pesaran CD 检验

* 4e. 多重共线性
estat vif             // VIF > 10 需处理

* 4f. 模型设定
estat ovtest          // Ramsey RESET
linktest

* 4g. 平稳性
dfuller y, lags(4) trend        // ADF
kpss y, maxlag(4)               // KPSS
pperron y, lags(4)              // Phillips–Perron

* 4h. 面板单位根
xtunitroot ips y, lags(aic 4)   // Im–Pesaran–Shin
xtunitroot llc y, lags(aic 4)   // Levin–Lin–Chu

* 4i. Hausman 检验（FE vs RE）
quietly xtreg y x1 x2, fe
estimates store fe
quietly xtreg y x1 x2, re
estimates store re
hausman fe re, sigmamore
```

## 决策表

| 检验 | 原假设 H₀ | 若拒绝则 |
|------|-----------|---------|
| `swilk` / `sktest` | 残差服从正态分布 | 大样本通常忽略；小样本用 bootstrap |
| `estat hettest` / `imtest, white` | 同方差 | 使用 `vce(robust)` 或 `vce(cluster id)` |
| `xtserial` / `xttest3` | 无面板自相关 / 无组间异方差 | 按个体聚类标准误 |
| `xtcsd, pesaran` | 无横截面相关 | 使用 Driscoll–Kraay 或 `xtscc` |
| `estat vif` > 10 | — | 删除或合并共线变量 |
| `estat ovtest` | 模型设定正确 | 加入多项式项或对数变换 |
| `dfuller` 拒绝 + `kpss` 不拒绝 | 序列平稳 | 使用水平值 |
| `dfuller` 不拒绝 | 存在单位根 | 一阶差分或协整 |
| `hausman` | RE 一致有效 | 使用 FE |

> 来源: [Awesome-Agent-Skills-for-Empirical-Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research), skill 00.2
