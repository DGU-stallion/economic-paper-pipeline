* ============================================
* 基准实证分析 do-file
* 项目：digital-supply-chain
* ============================================

clear all
set more off
set varabbrev off

* --- 自动检测项目根目录（当前do-file所在位置向上2级）
local do_file_path = c(tmpdir)  // fallback
capture local do_file_path = substr("`c(tmpdir)'", 1, strpos("`c(tmpdir)'", "do-files")-1)

* --- 用户可手动修改此处
global PROJECT_ROOT "D:/Project/economic-paper-pipeline/papers/digital-supply-chain"
global DATA "$PROJECT_ROOT/data/clean"
global OUTPUT "$PROJECT_ROOT/analysis/output"

capture mkdir "$OUTPUT"

use "$DATA/panel_clean.dta", clear

* --- T1: 描述性统计 ---
display "=== T1: 描述性统计 ==="
estpost summarize scr dt process innov info_share lev indep size age roa, detail
esttab using "$OUTPUT/t1_summary.tex", ///
    cells("count(fmt(%9.0f)) mean(fmt(%9.3f)) sd(fmt(%9.3f)) min(fmt(%9.3f)) p50(fmt(%9.3f)) max(fmt(%9.3f))") ///
    title("Descriptive Statistics") replace nonumber

* --- T2: 基准回归 M1→M6 ---
display "=== T2: 基准回归 ==="

* M1: 零控 (仅个体FE)
eststo M1: xtreg scr dt, fe vce(cluster id)

* M2: +财务治理
eststo M2: xtreg scr dt lev indep, fe vce(cluster id)

* M3: +企业特征
eststo M3: xtreg scr dt lev indep size age, fe vce(cluster id)

* M4: +盈利能力 (全变量 + 个体FE)
eststo M4: xtreg scr dt lev indep size age roa, fe vce(cluster id)

* M5: +年份效应 (双向FE)
eststo M5: xtreg scr dt lev indep size age roa i.year, fe vce(cluster id)

* M6: M5 即完整模型
eststo M6: xtreg scr dt lev indep size age roa i.year, fe vce(cluster id)

* 输出回归表
esttab M1 M2 M3 M4 M5 M6 using "$OUTPUT/t2_baseline.tex", ///
    keep(dt lev indep size age roa) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    b(3) se(3) ///
    stats(N r2_w, fmt(%9.0f %9.3f) labels("Observations" "Within R²")) ///
    mtitle("M1" "M2" "M3" "M4" "M5" "M6") ///
    title("Baseline Regression: Digital Transformation and Supply Chain Resilience") ///
    replace

display "=== 基准回归完成 ==="
