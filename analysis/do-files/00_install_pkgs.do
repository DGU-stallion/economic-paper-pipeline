* 逐个安装核心包
cap ssc install estout, replace
if _rc != 0 {
    display as error "estout install failed: rc=" _rc
}
else {
    display as result "estout installed successfully"
}

cap ssc install coefplot, replace
if _rc != 0 {
    display as error "coefplot install failed: rc=" _rc
}
else {
    display as result "coefplot installed successfully"
}

cap ssc install winsor2, replace
if _rc != 0 {
    display as error "winsor2 install failed: rc=" _rc
}
else {
    display as result "winsor2 installed successfully"
}

cap ssc install outreg2, replace
if _rc != 0 {
    display as error "outreg2 install failed: rc=" _rc
}
else {
    display as result "outreg2 installed successfully"
}

cap ssc install reghdfe, replace
if _rc != 0 {
    display as error "reghdfe install failed: rc=" _rc
}
else {
    display as result "reghdfe installed successfully"
}
