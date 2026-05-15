# 必需 Stata 包

首次安装后运行一次以下命令：

```stata
ssc install reghdfe,             replace
ssc install ftools,              replace       // reghdfe / ivreg2 依赖
ssc install ivreg2,              replace
ssc install ranktest,            replace       // ivreg2 依赖
ssc install ivreghdfe,           replace       // 高维 FE IV
ssc install ppmlhdfe,            replace       // 高维 FE 泊松
ssc install csdid,               replace       // Callaway–Sant'Anna (2021)
ssc install drdid,               replace       // csdid 依赖
ssc install did_imputation,      replace       // Borusyak et al. (2024)
ssc install eventstudyinteract,  replace       // Sun & Abraham (2021)
ssc install sdid,                replace       // 合成 DID
ssc install did_multiplegt_dyn,  replace       // de Chaisemartin & D'Haultfœuille
ssc install bacondecomp,         replace       // Goodman-Bacon (2021)
ssc install honestdid,           replace       // Rambachan–Roth 平行趋势敏感性
ssc install rdrobust,            replace       // Calonico–Cattaneo–Titiunik RD
ssc install rddensity,           replace       // McCrary 密度检验
ssc install synth,               replace       // 合成控制法
ssc install synth_runner,        replace       // SCM + 安慰剂检验
ssc install psmatch2,            replace       // 倾向得分匹配
ssc install ebalance,            replace       // 熵平衡
ssc install coefplot,            replace
ssc install estout,              replace       // estout / esttab / eststo
ssc install outreg2,             replace
ssc install asdoc,               replace       // Word/Excel 表格
ssc install binscatter,          replace
ssc install balancetable,        replace
ssc install winsor2,             replace
ssc install boottest,            replace       // wild cluster bootstrap
ssc install ritest,              replace       // 随机化推断
ssc install rwolf,               replace       // Romano–Wolf 多重检验
ssc install moremata,            replace       // Mata 扩展
ssc install mdesc,               replace       // 缺失值描述
ssc install missings,            replace
ssc install unique,              replace       // 面板唯一 ID
ssc install schemepack,          replace       // 现代出版级配色
```

> 来源: [Awesome-Agent-Skills-for-Empirical-Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research), skill 00.2
