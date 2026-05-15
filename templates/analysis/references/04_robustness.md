# 稳健性检验模板

## 6a. 渐进控制规范（M1→M6）

```stata
eststo clear
eststo m1: qui reg    y treat, vce(cluster id)
eststo m2: qui reg    y treat x1 x2, vce(cluster id)
eststo m3: qui reghdfe y treat x1 x2, absorb(id) vce(cluster id)
eststo m4: qui reghdfe y treat x1 x2, absorb(id year) vce(cluster id)
eststo m5: qui reghdfe y treat x1 x2, absorb(id year region) vce(cluster id)
eststo m6: qui reghdfe y treat x1 x2, ///
    absorb(id year i.industry#i.year) vce(cluster id)
esttab m1 m2 m3 m4 m5 m6 using "analysis/output/table2_main.tex", ///
    replace se star(* 0.10 ** 0.05 *** 0.01) ///
    stats(N r2 r2_a, labels("N" "R²" "Adj. R²")) ///
    label booktabs
```

## 6b. 替代聚类水平

```stata
foreach c in id firm industry state {
    qui reghdfe y treat, absorb(id year) vce(cluster `c')
    display "cluster=`c'  b=" _b[treat] "  se=" _se[treat]
}
```

## 6c. Wild Cluster Bootstrap（聚类较少时）

```stata
qui reghdfe y treat, absorb(id year) vce(cluster state)
boottest treat, cluster(state) reps(9999) seed(42)
```

## 6d. 子样本分割

```stata
foreach mask in "female==0" "female==1" "age<median" "age>=median" {
    qui reghdfe y treat if `mask', absorb(id year) vce(cluster id)
    display "`mask': b=" _b[treat] "  se=" _se[treat] "  N=" e(N)
}
```

## 6e. 安慰剂时间

```stata
gen fake_first = first_treat - 3
gen fake_post  = (year >= fake_first)
preserve
    keep if year < first_treat
    reghdfe y fake_post, absorb(id year) vce(cluster id)
restore
```

## 6f. 随机化推断

```stata
ritest treat _b[treat], reps(1000) seed(0) ///
    strata(id): reghdfe y treat, absorb(id year) vce(cluster id)
```

## 6g. Romano–Wolf 多重检验

```stata
rwolf y1 y2 y3, indepvar(treat) ///
    controls(x1 x2) reps(500) seed(42) method(reghdfe) ///
    fe(id year) cluster(id)
```

## 6h. TWFE 偏差诊断

```stata
* Bacon 分解（Goodman-Bacon）
bacondecomp y treat, ddetail

* HonestDiD（Rambachan–Roth 平行趋势敏感性）
* （先运行事件研究并保存 b/V）
honestdid, pre(1/4) post(5/9) mvec(0(0.1)0.5)
```

## 6i. Oster (2019) δ*

```stata
* 短回归
qui reg y treat
scalar bs = _b[treat]
* 长回归（含所有控制变量和 FE）
qui reghdfe y treat x1 x2, absorb(id year)
scalar bl = _b[treat]
psacalc delta treat, mcontrol(x1 x2) rmax(1.3*e(r2))
```

> 来源: [Awesome-Agent-Skills-for-Empirical-Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research), skill 00.2
