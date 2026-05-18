* ============================================
* 稳健性检验
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

* --- 基准模型(作为参照) ---
display "=== 基准模型 ==="
eststo base: xtreg scr dt $CTRL, fe vce(cluster id)

* --- R1: 替换 D 为滞后一期 ---
display "=== R1: 滞后D ==="
gen dt_lag = L.dt
eststo R1: xtreg scr dt_lag $CTRL, fe vce(cluster id)

* --- R2: 剔除 2020 年 ---
display "=== R2: 剔除2020 ==="
eststo R2: xtreg scr dt $CTRL if year != 2020, fe vce(cluster id)

* --- R3: 仅疫情前样本 ---
display "=== R3: 仅2015-2019 ==="
eststo R3: xtreg scr dt $CTRL if year <= 2019, fe vce(cluster id)

* --- R4: 替换 Y 为对数 ---
display "=== R4: ln(scr) ==="
gen lnscr = ln(scr + 1)
eststo R4: xtreg lnscr dt $CTRL, fe vce(cluster id)

* --- 输出稳健性检验表 ---
esttab base R1 R2 R3 R4 ///
    using "$OUTPUT/t5_robustness.tex", ///
    keep(dt dt_lag) ///
    star(* 0.10 ** 0.05 *** 0.01) b(3) se(3) ///
    stats(N r2_w, fmt(%9.0f %9.3f) labels("Observations" "Within R²")) ///
    mtitle("基准" "滞后D" "剔2020" "仅2015-19" "ln(Y)") ///
    title("Robustness Checks") replace

display "=== 稳健性检验完成 ==="
