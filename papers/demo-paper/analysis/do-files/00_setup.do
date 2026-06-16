* 安装实证分析必需包
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install coefplot, replace
ssc install outreg2, replace
ssc install mdesc, replace
ssc install winsor2, replace
ssc install schemepack, replace

* 验证数据（路径由 PROJECT_ROOT 环境变量或当前工作目录决定）
global DATA_DIR "$PROJECT_ROOT/data/clean"
use "$DATA_DIR/panel_clean.dta", clear
describe
sum
