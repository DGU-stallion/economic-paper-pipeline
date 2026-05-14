/*===========================================================================
 * 05_heterogeneity.do — 异质性分析（东中西分样本）
 * 产出: T5 异质性回归表 + F2-F4 异质性图
 *===========================================================================*/

clear all
set more off
capture log close

local datadir "D:/Project/economic-paper-pipeline/data/clean"
local outdir  "D:/Project/economic-paper-pipeline/analysis/output"
local logdir  "D:/Project/economic-paper-pipeline/analysis/logs"

log using "`logdir'/05_heterogeneity.log", replace text

use "`datadir'/china_provincial_panel.dta", clear

* ── 面板设定 ──────────────────────────────────────────────
encode province_en, gen(provid)
xtset provid year

* ── 变量准备 ──────────────────────────────────────────────
global Y  tertiary_employment_share
global D  digital_economy_index
global CTRLS gdp_percapita fixed_capital_investment export_share government_expenditure ///
    internet_penetration mobile_phone_penetration education_expenditure education_share

foreach v in $Y $D digital_finance_index $CTRLS urbanization_rate {
    winsor2 `v', replace cuts(1 99)
}

* ── 区域标签 ──────────────────────────────────────────────
label define region_lbl 1 "东部" 2 "中部" 3 "西部"
label values region region_lbl

* ════════════════════════════════════════════════════════════
* T5: 东中西分样本回归
* ════════════════════════════════════════════════════════════

eststo clear

* 全样本基准
eststo full: xtreg $Y $D $CTRLS i.year, fe vce(cluster provid)

* 东部 (region==1)
eststo east: xtreg $Y $D $CTRLS i.year if region==1, fe vce(cluster provid)

* 中部 (region==2)
eststo central: xtreg $Y $D $CTRLS i.year if region==2, fe vce(cluster provid)

* 西部 (region==3)
eststo west: xtreg $Y $D $CTRLS i.year if region==3, fe vce(cluster provid)

* ── 导出 T5 ──────────────────────────────────────────────
esttab full east central west using "`outdir'/table5_heterogeneity.tex", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    keep($D $CTRLS) ///
    order($D) ///
    mtitles("全样本" "东部" "中部" "西部") ///
    scalars("N Observations" "r2_w Within R2") ///
    sfmt(%9.0f %9.3f) ///
    title(异质性分析：东中西分样本回归\label{tab:heterogeneity}) ///
    addnotes("注：所有模型均包含控制变量、省份固定效应和年份固定效应，省份聚类标准误。" ///
             "东部11省、中部8省、西部12省。" ///
             "* p$<$0.10, ** p$<$0.05, *** p$<$0.01") ///
    label booktabs nonote

display "T5 saved: `outdir'/table5_heterogeneity.tex"

* ════════════════════════════════════════════════════════════
* F2: 东中西系数对比图
* ════════════════════════════════════════════════════════════

coefplot (full, label(全样本) lcolor(black) ciopts(lcolor(black))) ///
    (east, label(东部) lcolor(blue) ciopts(lcolor(blue))) ///
    (central, label(中部) lcolor(green) ciopts(lcolor(green))) ///
    (west, label(西部) lcolor(orange) ciopts(lcolor(orange))), ///
    keep($D) vertical ///
    yline(0, lpattern(dash) lcolor(gray)) ///
    title("数字经济系数: 东中西对比") ///
    ytitle("系数 + 95% CI") ///
    scheme(s2color)
graph export "`outdir'/fig2_heterogeneity_coef.pdf", replace

display "F2 saved: `outdir'/fig2_heterogeneity_coef.pdf"

* ════════════════════════════════════════════════════════════
* F3: 东中西三产就业趋势对比
* ════════════════════════════════════════════════════════════

preserve
collapse (mean) $Y, by(year region)
twoway (line $Y year if region==1, lcolor(blue) lpattern(solid)) ///
       (line $Y year if region==2, lcolor(green) lpattern(dash)) ///
       (line $Y year if region==3, lcolor(orange) lpattern(dot)), ///
    title("三产就业占比趋势: 东中西对比 (2011-2023)") ///
    ytitle("三产就业占比均值") xtitle("年份") ///
    legend(order(1 "东部" 2 "中部" 3 "西部") rows(1)) ///
    scheme(s2color)
graph export "`outdir'/fig3_employment_trend.pdf", replace

display "F3 saved: `outdir'/fig3_employment_trend.pdf"
restore

* ════════════════════════════════════════════════════════════
* F4: 数字经济趋势对比
* ════════════════════════════════════════════════════════════

preserve
collapse (mean) $D, by(year region)
twoway (line $D year if region==1, lcolor(blue) lpattern(solid)) ///
       (line $D year if region==2, lcolor(green) lpattern(dash)) ///
       (line $D year if region==3, lcolor(orange) lpattern(dot)), ///
    title("数字经济指数趋势: 东中西对比 (2011-2023)") ///
    ytitle("数字经济指数均值") xtitle("年份") ///
    legend(order(1 "东部" 2 "中部" 3 "西部") rows(1)) ///
    scheme(s2color)
graph export "`outdir'/fig4_digital_trend.pdf", replace

display "F4 saved: `outdir'/fig4_digital_trend.pdf"
restore

* ── 补充：区域间系数差异的 Wald 检验 ─────────────────────
display "=== 区域汇总 ==="
tab region
display "东部省份:"
tab province if region==1
display "中部省份:"
tab province if region==2
display "西部省份:"
tab province if region==3

log close
