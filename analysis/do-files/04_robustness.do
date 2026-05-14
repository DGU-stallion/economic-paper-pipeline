/*===========================================================================
 * 04_robustness.do — 稳健性检验
 * 产出: T4 稳健性检验汇总表
 *===========================================================================*/

clear all
set more off
capture log close

local datadir "D:/Project/economic-paper-pipeline/data/clean"
local outdir  "D:/Project/economic-paper-pipeline/analysis/output"
local logdir  "D:/Project/economic-paper-pipeline/analysis/logs"

log using "`logdir'/04_robustness.log", replace text

use "`datadir'/china_provincial_panel.dta", clear

* ── 面板设定 ──────────────────────────────────────────────
encode province_en, gen(provid)
xtset provid year

* ── 变量准备 ──────────────────────────────────────────────
global Y  tertiary_employment_share
global D  digital_economy_index
global D_alt digital_finance_index
global CTRLS gdp_percapita fixed_capital_investment export_share government_expenditure ///
    internet_penetration mobile_phone_penetration education_expenditure education_share

foreach v in $Y $D $D_alt $CTRLS urbanization_rate {
    winsor2 `v', replace cuts(1 99)
}

* 生成对数转换变量
gen ln_gdp_percapita = ln(gdp_percapita)
gen ln_education_expenditure = ln(education_expenditure)
label var ln_gdp_percapita "ln(人均GDP)"
label var ln_education_expenditure "ln(教育支出)"

* ════════════════════════════════════════════════════════════
* T4: 稳健性检验汇总
* ════════════════════════════════════════════════════════════

eststo clear

* R1: 基准模型（M6 双向FE，用于对比）
eststo r1: xtreg $Y $D $CTRLS i.year, fe vce(cluster provid)

* R2: 替换核心解释变量 D → digital_finance_index
eststo r2: xtreg $Y $D_alt $CTRLS i.year, fe vce(cluster provid)

* R3: 剔除直辖市（北京、天津、上海）
gen is_municipality = (province == "北京市" | province == "天津市" | province == "上海市")
eststo r3: xtreg $Y $D $CTRLS i.year if is_municipality==0, fe vce(cluster provid)

* R4: 对数变换（部分变量取对数）
eststo r4: xtreg $Y $D ln_gdp_percapita fixed_capital_investment export_share ///
    government_expenditure internet_penetration mobile_phone_penetration ///
    ln_education_expenditure education_share i.year, fe vce(cluster provid)

* R5: 剔除 COVID 年份 (2020)，检验特殊时期影响
eststo r5: xtreg $Y $D $CTRLS i.year if year != 2020, fe vce(cluster provid)

* R6: 缩尾 5% 替代 1%
foreach v in $Y $D $D_alt $CTRLS urbanization_rate {
    winsor2 `v', replace cuts(5 95)
}
eststo r6: xtreg $Y $D $CTRLS i.year, fe vce(cluster provid)

* ── 导出 T4 ──────────────────────────────────────────────
esttab r1 r2 r3 r4 r5 r6 using "`outdir'/table4_robustness.tex", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    keep($D $D_alt ln_gdp_percapita) ///
    order($D $D_alt) ///
    mtitles("基准" "替换D" "剔除直辖市" "对数变换" "剔除COVID" "5%缩尾") ///
    scalars("N Observations") ///
    sfmt(%9.0f) ///
    title(稳健性检验\label{tab:robustness}) ///
    addnotes("注：所有模型均包含控制变量、省份固定效应和年份固定效应，省份聚类标准误。" ///
             "R1基准模型，R2替换核心解释变量为数字金融指数，R3剔除北京/天津/上海三个直辖市。" ///
             "R4对数变换人均GDP和教育支出，R5剔除2020年，R6使用5%缩尾替代1%。" ///
             "* p$<$0.10, ** p$<$0.05, *** p$<$0.01") ///
    label booktabs nonote

display "T4 saved: `outdir'/table4_robustness.tex"

* ── 补充：原始变量系数也被输出（用于完整检查） ────────────
esttab r1 r2 r3 r4 r5 r6 using "`outdir'/table4_robustness_full.tex", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    mtitles("基准" "替换D" "剔除直辖市" "对数变换" "剔除COVID" "5%缩尾") ///
    title(稳健性检验（完整结果）\label{tab:robustness_full}) ///
    addnotes("* p$<$0.10, ** p$<$0.05, *** p$<$0.01") ///
    label booktabs nonote

display "T4 full saved: `outdir'/table4_robustness_full.tex"

log close
