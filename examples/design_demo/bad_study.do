* design_demo — intentionally flawed study (the lint must catch all three)
* 12 provinces, treatment rolled out in 2003/2006/2009 (staggered adoption)
import delimited "panel.csv", clear
gen post = year >= treat_year
gen did = post * treated
reghdfe lr_sales did ln_hp i.year, absorb(city year) vce(cluster state)
estimates store twfe
