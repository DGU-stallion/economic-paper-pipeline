* ============================================
* 数据清洗 do-file (通用模板，零硬编码)
* 占位符由 pipeline.py gen-do 自动替换
* ============================================

clear all
set more off
set varabbrev off

* --- 全局设置 ---
global PROJECT_ROOT "D:/Project/economic-paper-pipeline/papers/digital-supply-chain"
global RAW_DATA   "$PROJECT_ROOT/data/raw"
global CLEAN_DATA "$PROJECT_ROOT/data/clean"

capture mkdir "$CLEAN_DATA"

* --- S1: 自动检测 Excel sheet ---
local excel_file "$RAW_DATA/{data.xlsx}"
capture {
    import excel using "`excel_file'", describe
    local sheet_count = r(N_sheets)
    local sheet_name = r(sheet_1)
    display "检测到 `sheet_count' 个 Excel sheet, 使用: `sheet_name'"
}

* --- S2: 导入数据 ---
import excel using "`excel_file'", sheet("`sheet_name'") firstrow clear

* --- S3: 字符串变量安全编码 ---
foreach var of varlist _all {
    local type: type `var'
    if substr("`type'", 1, 3) == "str" {
        if strpos(lower("`var'"), "id") > 0 | strpos(lower("`var'"), "code") > 0 | strpos(lower("`var'"), "stkcd") > 0 {
            capture confirm numeric variable `var'
            if _rc != 0 {
                display "编码字符串ID变量: `var'"
                encode `var', gen(`var'_num)
                drop `var'
                rename `var'_num `var'
            }
        }
    }
}

* --- S4: 手动缩尾 (零外部依赖) ---
local winsor_vars "scr dt   "
* 补充：自动检测其他连续变量
foreach var of varlist _all {
    capture confirm numeric variable `var'
    if _rc == 0 {
        quietly count if `var' != .
        quietly tabulate `var'
        if r(r) > 100 & strpos(lower("`var'"), "year") == 0 & strpos(lower("`var'"), "id") == 0 {
            local already = 0
            foreach wv in `winsor_vars' {
                if "`var'" == "`wv'" local already = 1
            }
            if `already' == 0 {
                local winsor_vars "`winsor_vars' `var'"
            }
        }
    }
}

foreach var in `winsor_vars' {
    capture confirm numeric variable `var'
    if _rc == 0 {
        _pctile `var', p(1 99)
        if r(r1) < . & r(r2) < . {
            replace `var' = r(r1) if `var' < r(r1)
            replace `var' = r(r2) if `var' > r(r2)
            display "  `var': p1=" %9.4f r(r1) ", p99=" %9.4f r(r2)
        }
    }
}

* --- S5: 面板设定 ---
local id_var "id"
local year_var "year"
if "`id_var'" != "" & "`year_var'" != "" {
    display "面板设定: `id_var' × `year_var'"
    xtset `id_var' `year_var'
}

* --- S6: 描述性统计 ---
eststo clear
estpost summarize _all
esttab using "$CLEAN_DATA/desc_stats.tex", replace ///
    cells("mean(fmt(3)) sd(fmt(3)) min(fmt(3)) max(fmt(3)) count(fmt(0))") ///
    title("Descriptive Statistics") label noobs compress

* --- S7: 保存 ---
save "$CLEAN_DATA/panel_clean.dta", replace

display "=== 清洗完成 ==="
display "观测值: " c(N)
display "变量数: " c(k)
