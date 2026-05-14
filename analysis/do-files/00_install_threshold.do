cap ssc install xthreg, replace
if _rc != 0 {
    display as error "xthreg install failed: rc=" _rc
}
else {
    display as result "xthreg installed"
}

cap ssc install xttest3, replace
if _rc != 0 {
    display as error "xttest3 install failed: rc=" _rc
}
else {
    display as result "xttest3 installed"
}

* 检查 xthreg 可用性
cap which xthreg
if _rc != 0 display "xthreg NOT found"
else display "xthreg OK"
