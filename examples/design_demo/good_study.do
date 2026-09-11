* design_demo — referee-ready study (the lint should be CLEAN)
* 230 clusters, staggered adoption handled with CS estimator + wild bootstrap
import delimited "panel.csv", clear
gen gvar = treat_year
replace gvar = 0 if treat_year == .
csdid lr_sales ln_hp i.year, ivar(city) time(year) gvar(gvar) method(dripw)
estat event
boottest did, cluster(state) reps(9999)
