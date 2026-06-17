* 补充：M1→M6 系数对比图
clear all
set more off

local datadir "D:/Project/economic-paper-pipeline/data/clean"
local outdir  "D:/Project/economic-paper-pipeline/analysis/output"

use "`datadir'/china_provincial_panel.dta", clear
encode province_en, gen(provid)
xtset provid year

global Y  tertiary_employment_share
global D  digital_economy_index
global CTRLS gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration education_expenditure education_share

foreach v in $Y $D $CTRLS urbanization_rate {
    winsor2 `v', replace cuts(1 99)
}

eststo clear
eststo m1: reg $Y $D, vce(cluster provid)
eststo m2: reg $Y $D gdp_percapita fixed_capital_investment export_share government_expenditure, vce(cluster provid)
eststo m3: reg $Y $D gdp_percapita fixed_capital_investment export_share government_expenditure internet_penetration mobile_phone_penetration, vce(cluster provid)
eststo m4: reg $Y $D $CTRLS, vce(cluster provid)
eststo m5: xtreg $Y $D $CTRLS, fe vce(cluster provid)
eststo m6: xtreg $Y $D $CTRLS i.year, fe vce(cluster provid)

coefplot m1 || m2 || m3 || m4 || m5 || m6, ///
    keep($D) vertical ///
    yline(0, lpattern(dash) lcolor(gray)) ///
    title("数字经济系数：M1→M6 渐进控制") ///
    legend(order(1 "M1: 双变量" 2 "M2: +经济控制" 3 "M3: +数字设施" 4 "M4: +人力资本" 5 "M5: +省份FE" 6 "M6: +年份FE") rows(2)) ///
    scheme(s2color)
graph export "`outdir'/fig3_coefplot.pdf", replace

display "F3 saved: `outdir'/fig3_coefplot.pdf"
