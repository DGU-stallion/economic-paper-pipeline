* ============================================
* 补全表格与图表
* ============================================

clear all
set more off
cap noi ssc install estout, replace
cap noi ssc install coefplot, replace

use "D:/Project/economic-paper-pipeline/papers/digital-supply-chain/data/clean/panel_clean.dta", clear
global CTRL "lev indep size age roa i.year"

* --- T3: 中介效应汇总表 ---
* 重新跑三路径
* 总效应
xtreg scr dt $CTRL, fe vce(cluster id)
eststo total

* 路径1
xtreg scr dt process $CTRL, fe vce(cluster id)
eststo med1

* 路径2
xtreg scr dt innov $CTRL, fe vce(cluster id)
eststo med2

* 路径3
xtreg scr dt info_share $CTRL, fe vce(cluster id)
eststo med3

* 三路径联合
xtreg scr dt process innov info_share $CTRL, fe vce(cluster id)
eststo med_all

esttab total med1 med2 med3 med_all ///
    using "D:/Project/economic-paper-pipeline/papers/digital-supply-chain/paper/tables/t3_mediation.tex", ///
    keep(dt process innov info_share) ///
    star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_w, fmt(%9.0f %9.3f) labels("Observations" "Within R²")) ///
    mtitle("总效应" "+流程优化" "+创新能力" "+信息共享" "全部中介") ///
    title("Mediation Analysis: Three Transmission Channels") ///
    replace

* --- Figure 1: 基准回归系数演进 (M1-M6) ---
eststo clear
xtreg scr dt, fe vce(cluster id)
eststo m1
xtreg scr dt lev indep, fe vce(cluster id)
eststo m2
xtreg scr dt lev indep size age, fe vce(cluster id)
eststo m3
xtreg scr dt lev indep size age roa, fe vce(cluster id)
eststo m4
xtreg scr dt lev indep size age roa i.year, fe vce(cluster id)
eststo m5

coefplot (m1, label("M1: 零控") offset(-0.3)) ///
         (m2, label("M2: +财务") offset(-0.15)) ///
         (m3, label("M3: +企业特征")) ///
         (m4, label("M4: 全变量") offset(0.15)) ///
         (m5, label("M5: 双向FE") offset(0.3)), ///
    keep(dt) vertical xline(0) ///
    title("数字化转型对供应链韧性的基准回归系数") ///
    ytitle("DT系数 (95% CI)") ///
    scheme(s2color) ///
    graphregion(color(white))

graph export "D:/Project/economic-paper-pipeline/papers/digital-supply-chain/paper/figures/fig1_baseline_coef.pdf", replace

* --- Figure 2: 异质性森林图 ---
eststo clear

* 全样本
xtreg scr dt $CTRL, fe vce(cluster id)
eststo full

* 大规模
egen sz_med = median(size)
xtreg scr dt $CTRL if size > sz_med, fe vce(cluster id)
eststo large

* 小规模
xtreg scr dt $CTRL if size <= sz_med, fe vce(cluster id)
eststo small

* 高杠杆
egen lv_med = median(lev)
xtreg scr dt $CTRL if lev > lv_med, fe vce(cluster id)
eststo hlev

* 低杠杆
xtreg scr dt $CTRL if lev <= lv_med, fe vce(cluster id)
eststo llev

* 疫情后
gen pc = (year >= 2020)
xtreg scr dt $CTRL if pc==1, fe vce(cluster id)
eststo post

* 疫情前
xtreg scr dt $CTRL if pc==0, fe vce(cluster id)
eststo pre

coefplot (full, label("全样本") offset(-0.4)) ///
         (large, label("大规模") offset(-0.2)) ///
         (small, label("小规模")) ///
         (hlev, label("高杠杆") offset(0.2)) ///
         (llev, label("低杠杆") offset(0.4)), ///
    keep(dt) vertical xline(0) ///
    title("企业规模与财务杠杆异质性") ///
    ytitle("DT系数 (95% CI)") ///
    scheme(s2color) ///
    graphregion(color(white))

graph export "D:/Project/economic-paper-pipeline/papers/digital-supply-chain/paper/figures/fig2_heterogeneity.pdf", replace

* --- Figure 3: 疫情前后对比 ---
coefplot (full, label("全样本") offset(-0.2)) ///
         (pre, label("疫情前") offset(0)) ///
         (post, label("疫情后") offset(0.2)), ///
    keep(dt) vertical xline(0) ///
    title("疫情前后数字化转型对供应链韧性的效应对比") ///
    ytitle("DT系数 (95% CI)") ///
    scheme(s2color) ///
    graphregion(color(white))

graph export "D:/Project/economic-paper-pipeline/papers/digital-supply-chain/paper/figures/fig3_covid.pdf", replace

display "=== 图表生成完成 ==="
