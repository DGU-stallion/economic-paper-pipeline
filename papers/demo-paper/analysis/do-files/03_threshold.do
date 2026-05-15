/*===========================================================================
 * 03_threshold.do — Hansen (1999) 面板门槛模型（手动实现）
 * 门槛变量: urbanization_rate
 * 产出: T3 门槛回归表 + F1 门槛图
 *===========================================================================*/

clear all
set more off
capture log close

local datadir "D:/Project/economic-paper-pipeline/data/clean"
local outdir  "D:/Project/economic-paper-pipeline/analysis/output"
local logdir  "D:/Project/economic-paper-pipeline/analysis/logs"

log using "`logdir'/03_threshold.log", replace text

use "`datadir'/china_provincial_panel.dta", clear

* ── 面板设定 ──────────────────────────────────────────────
encode province_en, gen(provid)
xtset provid year

* ── 变量准备 ──────────────────────────────────────────────
foreach v in tertiary_employment_share digital_economy_index digital_finance_index ///
    gdp_percapita fixed_capital_investment export_share government_expenditure ///
    internet_penetration mobile_phone_penetration education_expenditure education_share ///
    urbanization_rate {
    winsor2 `v', replace cuts(1 99)
}

global Y  tertiary_employment_share
global D  digital_economy_index
global Q  urbanization_rate          // 门槛变量
global CTRLS gdp_percapita fixed_capital_investment export_share government_expenditure ///
    internet_penetration mobile_phone_penetration education_expenditure education_share

* ════════════════════════════════════════════════════════════
* Step 1: 网格搜索最优门槛
* ════════════════════════════════════════════════════════════

* 先对门槛变量去重排序，找候选门槛
preserve
collapse (mean) $Q, by(provid)
sum $Q
restore

* 门槛搜索范围：剔除门槛变量两端各 5% 观测值
_pctile $Q, percentiles(5 95)
local q_min = r(r1)
local q_max = r(r2)
display "门槛搜索范围: [`q_min', `q_max']"

* 生成 200 个候选门槛点
local n_grid = 100
local step = (`q_max' - `q_min') / `n_grid'

* 网格搜索
tempname results
postfile `results' gamma rss1 using "`logdir'/threshold_grid.dta", replace

forvalues i = 1/`n_grid' {
    local gamma = `q_min' + `i' * `step'

    * 生成门槛虚拟变量
    gen low_regime = ($Q <= `gamma')

    * 交互项
    gen D_low  = $D * low_regime
    gen D_high = $D * (1 - low_regime)

    * FE 回归
    quietly xtreg $Y D_low D_high $CTRLS, fe
    local rss = e(rss)

    post `results' (`gamma') (`rss')

    drop low_regime D_low D_high
}

postclose `results'

* 找到最优门槛（RSS 最小化）
use "`logdir'/threshold_grid.dta", clear
sort rss1
local opt_gamma = gamma[1]
local min_rss = rss1[1]
display "最优门槛值: `opt_gamma'"
display "最小 RSS: `min_rss'"

* ── 绘制 F1: 门槛搜索图 ──────────────────────────────────
sum gamma
gen rss_ratio = rss1 / `min_rss'
twoway line rss_ratio gamma, ///
    xline(`opt_gamma', lpattern(dash) lcolor(red)) ///
    title("门槛搜索：RSS比率") ///
    xtitle("城镇化率门槛值") ytitle("RSS / Min RSS") ///
    note("最优门槛 = `opt_gamma'") ///
    scheme(s2color)
graph export "`outdir'/fig1_threshold.pdf", replace
display "F1 saved: `outdir'/fig1_threshold.pdf"

* ── 保存门槛值 ────────────────────────────────────────────
* 返回原数据
use "`datadir'/china_provincial_panel.dta", clear
encode province_en, gen(provid)
xtset provid year
foreach v in $Y $D digital_finance_index $CTRLS $Q {
    winsor2 `v', replace cuts(1 99)
}

* ════════════════════════════════════════════════════════════
* Step 2: 门槛回归（在最优门槛下）
* ════════════════════════════════════════════════════════════

* 门槛虚拟变量
gen low_regime  = ($Q <= `opt_gamma')
gen high_regime = ($Q > `opt_gamma')

gen D_low  = $D * low_regime
gen D_high = $D * high_regime

label var D_low  "数字经济 × 低城镇化"
label var D_high "数字经济 × 高城镇化"

display "=== 门槛回归: 城镇化率门槛 = `opt_gamma' ==="
display "低城镇化组样本比例: "
sum low_regime

* ── 门槛 FE 回归 ──────────────────────────────────────────
xtreg $Y D_low D_high $CTRLS i.year, fe vce(cluster provid)
estimates store threshold_fe

* ── 低/高两组分别回归 ─────────────────────────────────────
xtreg $Y $D $CTRLS i.year if low_regime==1, fe vce(cluster provid)
estimates store low_group

xtreg $Y $D $CTRLS i.year if high_regime==1, fe vce(cluster provid)
estimates store high_group

* ════════════════════════════════════════════════════════════
* T3: 门槛回归表
* ════════════════════════════════════════════════════════════

esttab threshold_fe low_group high_group using "`outdir'/table3_threshold.tex", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    keep(D_low D_high $D $CTRLS) ///
    order(D_low D_high $D) ///
    mtitles("全样本门槛" "低城镇化" "高城镇化") ///
    title(面板门槛回归：城镇化的调节效应\label{tab:threshold}) ///
    addnotes("注：门槛变量为城镇化率，最优门槛值为 `opt_gamma'。" ///
             "全样本门槛回归同时包含低/高两组数字经济的交互项。" ///
             "* p$<$0.10, ** p$<$0.05, *** p$<$0.01") ///
    label booktabs nonote

display "T3 saved: `outdir'/table3_threshold.tex"

* ════════════════════════════════════════════════════════════
* Step 3: Bootstrap 门槛显著性检验
* ════════════════════════════════════════════════════════════

* 原假设 H0: 无门槛效应（线性模型）
* 备择 H1: 存在单门槛

* 线性模型 RSS
xtreg $Y $D $CTRLS i.year, fe
local rss_linear = e(rss)

* 门槛模型 F 统计量
local F_threshold = ((`rss_linear' - `min_rss') / 1) / (`min_rss' / (e(N) - e(df_m) - 1))
display "F 统计量 = `F_threshold'"

* Bootstrap 抽样（省份聚类 bootstrap，固定门槛值）
local n_boot = 100
set seed 20260512

preserve
keep provid year $Y $D $CTRLS $Q low_regime D_low D_high

tempname boot_results
postfile `boot_results' boot_F using "`logdir'/threshold_boot.dta", replace

forvalues b = 1/`n_boot' {
    * 省份聚类 bootstrap
    bsample, cluster(provid) idcluster(newprovid)

    * 门槛模型 RSS (bootstrap)
    cap xtreg $Y D_low D_high $CTRLS, fe
    if _rc == 0 {
        local rss_thresh_boot = e(rss)
        * 线性模型 RSS (bootstrap)
        cap xtreg $Y $D $CTRLS, fe
        if _rc == 0 {
            local rss_linear_boot = e(rss)
            local F_boot = ((`rss_linear_boot' - `rss_thresh_boot') / 1) / (`rss_thresh_boot' / (e(N) - e(df_m) - 1))
        }
        else local F_boot = 0
    }
    else local F_boot = 0

    post `boot_results' (`F_boot')
}

postclose `boot_results'
restore

* ── Bootstrap p-value ──────────────────────────────────────
use "`logdir'/threshold_boot.dta", clear
sum boot_F
count
local nvalid = r(N)
count if boot_F > `F_threshold' & boot_F != .
local n_extreme = r(N)
local p_value = `n_extreme' / `nvalid'
display "Bootstrap p-value (H0: no threshold): " `p_value'
display "Valid bootstrap samples: " `nvalid'
display "F 统计量 (原始): " `F_threshold'

* ── F1 补充：Bootstrap 分布 ───────────────────────────────
histogram boot_F, frequency ///
    xline(`F_threshold', lpattern(dash) lcolor(red)) ///
    title("Bootstrap F 统计量分布") ///
    xtitle("F 统计量") ///
    note("红线为原始F统计量=`F_threshold', Bootstrap p=`p_value'") ///
    scheme(s2color)
graph export "`outdir'/fig1_threshold_bootstrap.pdf", replace

log close
