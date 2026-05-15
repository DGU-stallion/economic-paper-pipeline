* 安装实证分析必需包
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install coefplot, replace
ssc install outreg2, replace
ssc install mdesc, replace
ssc install winsor2, replace
ssc install schemepack, replace

* 验证数据
use "D:/Project/economic-paper-pipeline/data/clean/china_provincial_panel.dta", clear
describe
sum
