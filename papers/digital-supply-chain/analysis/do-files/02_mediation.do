* ============================================
* 中介效应分析 do-file (通用模板，零硬编码，零外部依赖)
* 占位符由 pipeline.py gen-do 自动替换
* ============================================

clear all
set more off
set varabbrev off

* --- 全局设置 ---
global PROJECT_ROOT "D:/Project/economic-paper-pipeline/papers/digital-supply-chain"
global DATA "$PROJECT_ROOT/data/clean"
global OUTPUT "$PROJECT_ROOT/analysis/output"

capture mkdir "$OUTPUT"

use "$DATA/panel_clean.dta", clear

* --- 变量定义 (已从 project_config.json 自动替换) ---
local Y "scr"
local X "dt"
local M "  "
local CONTROLS "lev indep size age roa"
local VCE "vce(cluster id)"

display "=== 中介效应检验：逐步法 + Sobel检验 ==="
display "Y  = `Y'"
display "D  = `X'"
display "M  = `M'"
display "X  = `CONTROLS'"
display ""

* --- 第一步：总效应检验 ---
display "【第一步】总效应 Y ~ D"
eststo clear
eststo step1: xtreg `Y' `X' `CONTROLS' i.year, fe `VCE'
local total_effect = _b[`X']
local total_se = _se[`X']
local total_p = 2 * ttail(e(df_r), abs(_b[`X']/_se[`X']))
display "总效应 = " %9.4f `total_effect' " (SE=" %9.4f `total_se' ", P=" %5.3f `total_p' ")"
display ""

* --- 对每个中介变量进行 Sobel 检验 ---
local mediator_num = 1
foreach med in `M' {
    if "`med'" == "" continue

    display "--------------------------------------------------"
    display "【中介变量 `mediator_num'】`med'"
    display "--------------------------------------------------"

    * 第二步：D -> M
    display ""
    display "第二步：`X' -> `med'"
    quietly eststo step2_`mediator_num': xtreg `med' `X' `CONTROLS' i.year, fe `VCE'
    local a = _b[`X']
    local se_a = _se[`X']
    local p_a = 2 * ttail(e(df_r), abs(_b[`X']/_se[`X']))
    display "  a = " %9.4f `a' " (SE=" %9.4f `se_a' ", P=" %5.3f `p_a' ")"

    * 第三步：Y = D + M
    display ""
    display "第三步：`Y' = `X' + `med'"
    quietly eststo step3_`mediator_num': xtreg `Y' `X' `med' `CONTROLS' i.year, fe `VCE'
    local c_prime = _b[`X']
    local b = _b[`med']
    local se_b = _se[`med']
    local p_b = 2 * ttail(e(df_r), abs(_b[`med']/_se[`med']))
    display "  c' = " %9.4f `c_prime'
    display "  b  = " %9.4f `b' " (SE=" %9.4f `se_b' ", P=" %5.3f `p_b' ")"

    * --- Sobel 检验 (手动计算) ---
    display ""
    display "【Sobel 检验】"
    local ind_effect = `a' * `b'
    local ind_se = sqrt((`b'^2 * `se_a'^2) + (`a'^2 * `se_b'^2))
    local z = `ind_effect' / `ind_se'
    local p = 2 * (1 - normal(abs(`z')))

    display "  间接效应 = " %9.4f `ind_effect'
    display "  标准误   = " %9.4f `ind_se'
    display "  Z 值    = " %9.4f `z'
    display "  P 值    = " %9.4f `p'

    if `p' < 0.01 {
        display "  结果    = *** 1% 水平显著 ***"
    }
    else if `p' < 0.05 {
        display "  结果    = ** 5% 水平显著 **"
    }
    else if `p' < 0.1 {
        display "  结果    = * 10% 水平显著 *"
    }
    else {
        display "  结果    = 不显著，中介效应不成立"
    }

    if abs(`total_effect') > 0 {
        local ratio = `ind_effect' / `total_effect'
        display "  中介占比 = " %5.1f (`ratio' * 100) "%"
    }

    local mediator_num = `mediator_num' + 1
    display ""
}

* --- 输出结果表 ---
esttab step1 step2_1 step3_1 using "$OUTPUT/mediation_results.tex", replace ///
    se star(* 0.1 ** 0.05 *** 0.01) ///
    keep(`X' `M') ///
    title("Mediation Analysis") label compress
eststo clear

display ""
display "=== 中介效应分析完成 ==="
display "结果: $OUTPUT/mediation_results.tex"
