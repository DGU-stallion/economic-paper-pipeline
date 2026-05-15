/*===========================================================================
 * 01_describe.do — 描述统计
 * 产出: T1 描述统计表 + 相关系数矩阵
 *===========================================================================*/

clear all
set more off
capture log close

* ── 路径设置 ──────────────────────────────────────────────
local datadir "D:/Project/economic-paper-pipeline/data/clean"
local outdir  "D:/Project/economic-paper-pipeline/analysis/output"
local logdir  "D:/Project/economic-paper-pipeline/analysis/logs"
cap mkdir "`outdir'"
cap mkdir "`logdir'"

log using "`logdir'/01_describe.log", replace text

use "`datadir'/china_provincial_panel.dta", clear

* ── 面板设定 ──────────────────────────────────────────────
cap ssc install unique, replace
encode province_en, gen(provid)
xtset provid year
unique provid
local nprov = r(unique)
unique year
local nyear = r(unique)
display "面板: `nprov' 省份 × `nyear' 年 = " _N " 观测值"

* ── 变量标签 ──────────────────────────────────────────────
label var tertiary_employment_share "三产就业占比"
label var internet_penetration       "互联网普及率"
label var mobile_phone_penetration   "移动电话普及率"
label var gdp_percapita              "人均GDP"
label var urbanization_rate          "城镇化率"
label var fixed_capital_investment   "固定资本形成率"
label var export_share               "出口占GDP比重"
label var government_expenditure     "政府支出占GDP比重"
label var education_expenditure      "教育支出(亿元)"
label var education_share            "教育支出占GDP比重"
label var digital_finance_index      "数字金融指数"
label var digital_economy_index      "数字经济指数"

* ── 核心变量列表（用于所有后续表格） ────────────────────────
global Y  tertiary_employment_share
global D  digital_economy_index
global D_alt digital_finance_index
global CTRLS gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration education_expenditure education_share
global THRESHOLD urbanization_rate

* ── Winsor 1% 缩尾 ────────────────────────────────────────
foreach v in $Y $D $D_alt $CTRLS $THRESHOLD {
    winsor2 `v', replace cuts(1 99)
}

* ════════════════════════════════════════════════════════════
* T1: 描述统计表
* ════════════════════════════════════════════════════════════

estpost tabstat $Y $D $D_alt $CTRLS $THRESHOLD, ///
    statistics(mean sd min max N) columns(statistics)

esttab using "`outdir'/table1_descriptive.tex", replace ///
    cells("mean(fmt(3)) sd(fmt(3)) min(fmt(3)) max(fmt(3)) count") ///
    nonumber nomtitle noobs ///
    title(描述统计) ///
    note("样本: 31省份 × 2011–2023年, N=403. 所有连续变量经1%缩尾处理.")

display "T1 saved: `outdir'/table1_descriptive.tex"

* ── 补充：面板组内/组间/总体方差分解 ──────────────────────
xtsum $Y $D $D_alt $CTRLS $THRESHOLD

* ════════════════════════════════════════════════════════════
* 相关系数矩阵
* ════════════════════════════════════════════════════════════

correlate $Y $D $D_alt $CTRLS $THRESHOLD
matrix C = r(C)
estpost correlate $Y $D $D_alt $CTRLS $THRESHOLD, matrix
esttab using "`outdir'/table1_correlation.tex", replace ///
    not unstack compress noobs ///
    title(相关系数矩阵) ///
    note("Pearson相关系数.")

display "Correlation matrix saved."

* ── VIF 检验（先跑一个完整OLS看共线性） ──────────────────
reg $Y $D $CTRLS
estat vif

* ── 按地区（东中西）分组均值 ──────────────────────────────
tabstat $Y $D $CTRLS $THRESHOLD, by(region) statistics(mean sd) columns(statistics) longstub

log close
