* 检查已安装包和基本数据
cap which reghdfe
if _rc != 0 display "reghdfe NOT installed"
else display "reghdfe OK"

cap which estout
if _rc != 0 display "estout NOT installed"
else display "estout OK"

cap which esttab
if _rc != 0 display "esttab NOT installed"
else display "esttab OK"

cap which coefplot
if _rc != 0 display "coefplot NOT installed"
else display "coefplot OK"

cap which outreg2
if _rc != 0 display "outreg2 NOT installed"
else display "outreg2 OK"

cap which winsor2
if _rc != 0 display "winsor2 NOT installed"
else display "winsor2 OK"

* 数据验证
use "D:/Project/economic-paper-pipeline/data/clean/china_provincial_panel.dta", clear
describe
sum
