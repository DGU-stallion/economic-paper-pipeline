* ============================================
* 异质性分析
* 项目：digital-supply-chain
* ============================================

clear all
set more off
set varabbrev off

* --- 项目路径设置
global PROJECT_ROOT "D:/Project/economic-paper-pipeline/papers/digital-supply-chain"
global DATA "$PROJECT_ROOT/data/clean"
global OUTPUT "$PROJECT_ROOT/analysis/output"

capture mkdir "$OUTPUT"

use "$DATA/panel_clean.dta", clear
global CTRL "lev indep size age roa i.year"

* --- 生成分组变量 ---
* 企业规模分组 (中位数)
egen size_med = median(size)
gen large_firm = (size > size_med)
label define large 0 "小规模" 1 "大规模"
label values large_firm large

* 杠杆分组
egen lev_med = median(lev)
gen high_lev = (lev > lev_med)

* 疫情前后
gen post_covid = (year >= 2020)
label define covid 0 "疫情前(2015-2019)" 1 "疫情后(2020-2024)"
label values post_covid covid

* ============================================
* H1: 企业规模异质性
* ============================================
display "=== H1: 企业规模异质性 ==="
display "--- 大规模企业 ---"
eststo H1_large: xtreg scr dt $CTRL if large_firm==1, fe vce(cluster id)

display "--- 小规模企业 ---"
eststo H1_small: xtreg scr dt $CTRL if large_firm==0, fe vce(cluster id)

* ============================================
* H2: 时间异质性 (疫情前后)
* ============================================
display "=== H2: 疫情前后 ==="
display "--- 疫情前 ---"
eststo H2_pre: xtreg scr dt $CTRL if post_covid==0, fe vce(cluster id)

display "--- 疫情后 ---"
eststo H2_post: xtreg scr dt $CTRL if post_covid==1, fe vce(cluster id)

* ============================================
* H3: 财务杠杆异质性
* ============================================
display "=== H3: 财务杠杆异质性 ==="
display "--- 高杠杆 ---"
eststo H3_highlev: xtreg scr dt $CTRL if high_lev==1, fe vce(cluster id)

display "--- 低杠杆 ---"
eststo H3_lowlev: xtreg scr dt $CTRL if high_lev==0, fe vce(cluster id)

* ============================================
* H4: 交互项检验（正式差异检验）
* ============================================
display "=== H4: 交互项检验 ==="

* 规模交互
gen dt_large = dt * large_firm
display "--- 规模交互 ---"
xtreg scr dt dt_large large_firm $CTRL, fe vce(cluster id)
eststo H4_size_int: xtreg scr dt dt_large large_firm $CTRL, fe vce(cluster id)

* 疫情交互
gen dt_covid = dt * post_covid
display "--- 疫情交互 ---"
xtreg scr dt dt_covid post_covid $CTRL, fe vce(cluster id)
eststo H4_covid_int: xtreg scr dt dt_covid post_covid $CTRL, fe vce(cluster id)

* ============================================
* 输出异质性表
* ============================================
esttab H1_large H1_small H2_pre H2_post H3_highlev H3_lowlev ///
    using "$OUTPUT/t4_heterogeneity.tex", ///
    keep(dt) star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_w, fmt(%9.0f %9.3f) labels("Observations" "Within R²")) ///
    mtitle("大规模" "小规模" "疫情前" "疫情后" "高杠杆" "低杠杆") ///
    title("Heterogeneity Analysis") replace

esttab H4_size_int H4_covid_int ///
    using "$OUTPUT/t4_interaction.tex", ///
    keep(dt dt_large dt_covid) star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_w, fmt(%9.0f %9.3f) labels("Observations" "Within R²")) ///
    mtitle("规模交互" "疫情交互") ///
    title("Interaction Effects") replace

display "=== 异质性分析完成 ==="
