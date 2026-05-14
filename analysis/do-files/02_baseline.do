/*===========================================================================
 * 02_baseline.do — 基准回归（双向固定效应 + M1→M6 渐进控制）
 * 产出: T2 核心回归表 + 诊断检验
 *===========================================================================*/

clear all
set more off
capture log close

local datadir "D:/Project/economic-paper-pipeline/data/clean"
local outdir  "D:/Project/economic-paper-pipeline/analysis/output"
local logdir  "D:/Project/economic-paper-pipeline/analysis/logs"

log using "`logdir'/02_baseline.log", replace text

use "`datadir'/china_provincial_panel.dta", clear

* ── 面板设定 ──────────────────────────────────────────────
encode province_en, gen(provid)
xtset provid year

* ── 变量标签与全局宏 ──────────────────────────────────────
label var tertiary_employment_share "三产就业占比"
label var digital_economy_index      "数字经济指数"
label var digital_finance_index      "数字金融指数"
label var gdp_percapita              "人均GDP"
label var urbanization_rate          "城镇化率"
label var fixed_capital_investment   "固定资本形成率"
label var export_share               "出口占GDP比重"
label var government_expenditure     "政府支出占GDP比重"
label var internet_penetration       "互联网普及率"
label var mobile_phone_penetration   "移动电话普及率"
label var education_expenditure      "教育支出(亿元)"
label var education_share            "教育支出占GDP比重"

global Y  tertiary_employment_share
global D  digital_economy_index
global D_alt digital_finance_index
global CTRLS gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration education_expenditure education_share

* ── Winsor 1% 缩尾 ────────────────────────────────────────
foreach v in $Y $D $D_alt $CTRLS urbanization_rate {
    winsor2 `v', replace cuts(1 99)
}

* ════════════════════════════════════════════════════════════
* T2: M1→M6 渐进控制回归表（核心！）
* ════════════════════════════════════════════════════════════

eststo clear

* M1: 原始双变量 OLS
eststo m1: reg $Y $D, vce(cluster provid)

* M2: +经济控制 (gdp, 固定资本, 出口, 政府支出)
eststo m2: reg $Y $D gdp_percapita fixed_capital_investment export_share government_expenditure, vce(cluster provid)

* M3: +数字基础设施 (互联网, 移动电话)
eststo m3: reg $Y $D gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration, vce(cluster provid)

* M4: +人力资本 (教育支出, 教育占比) → 完整OLS
eststo m4: reg $Y $D $CTRLS, vce(cluster provid)

* M5: +省份 FE（单向 panel FE）
eststo m5: xtreg $Y $D $CTRLS, fe vce(cluster provid)

* M6: +年份 FE → 双向 FE（最终基准模型）
eststo m6: xtreg $Y $D $CTRLS i.year, fe vce(cluster provid)

* ── 导出 T2 LaTeX 表 ──────────────────────────────────────
esttab m1 m2 m3 m4 m5 m6 using "`outdir'/table2_main.tex", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    keep($D gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration education_expenditure education_share) ///
    order($D gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration education_expenditure education_share) ///
    scalars("N Observations" "r2_a Adjusted R2" "r2_w Within R2") ///
    sfmt(%9.0f %9.3f %9.3f) ///
    mtitles("M1" "M2" "M3" "M4" "M5" "M6") ///
    title(数字经济发展对三产就业占比的影响：基准回归\label{tab:main}) ///
    addnotes("注：括号内为省份聚类稳健标准误。M1-M4为Pooled OLS，M5加入省份固定效应，M6加入省份和年份双向固定效应。" "所有连续变量经1\%缩尾处理。* p$<$0.10, ** p$<$0.05, *** p$<$0.01") ///
    label booktabs nonote

display "T2 saved: `outdir'/table2_main.tex"

* ════════════════════════════════════════════════════════════
* 诊断检验
* ════════════════════════════════════════════════════════════

* ── 使用 M6 模型进行诊断 ──────────────────────────────────
* 重新跑一个可预测残差的版本
xtreg $Y $D $CTRLS i.year, fe
predict resid, e

* 残差正态性
sktest resid

* 面板自相关 (Wooldridge)
* 先用 FE 残差做辅助回归
xtreg $Y $D $CTRLS i.year, fe
estimates store m6_full

* 异方差与截面相关
xttest3
* 注意: xtcsd 需要 xtcsd 包

* VIF
reg $Y $D $CTRLS
estat vif

* Hausman FE vs RE
quietly xtreg $Y $D $CTRLS, fe
estimates store fe_model
quietly xtreg $Y $D $CTRLS, re
estimates store re_model
hausman fe_model re_model, sigmamore

* ── 生成 F3: M1→M6 系数对比图 ────────────────────────────
coefplot m1 || m2 || m3 || m4 || m5 || m6, ///
    keep($D) vertical ///
    yline(0, lpattern(dash) lcolor(gray)) ///
    title("数字经济系数：M1→M6 渐进控制") ///
    legend(order(1 "M1: 双变量" 2 "M2: +经济控制" 3 "M3: +数字设施" 4 "M4: +人力资本" 5 "M5: +省份FE" 6 "M6: +年份FE") rows(2)) ///
    scheme(s2color)
graph export "`outdir'/fig3_coefplot.pdf", replace

display "F3 saved: `outdir'/fig3_coefplot.pdf"

log close
