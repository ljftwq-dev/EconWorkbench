import delimited "mpdta_data.csv", clear
csdid lemp, ivar(countyreal) time(year) gvar(firsttreat) method(dripw)
matrix bgt = e(b_attgt)
matrix Vgt = e(V_attgt)
matrix gtt = e(gtt)
local natt = 12
postfile hnd str24 term double estimate se pvalue using gt_results, replace
forvalues r = 1/`natt' {
    local g  = el(gtt, `r', 1)
    local t1 = el(gtt, `r', 3)
    if `t1' >= `g' {
        local est = el(bgt, 1, `r')
        local sev = sqrt(el(Vgt, `r', `r'))
        local pv  = 2 * normal(-abs(`est' / `sev'))
        post hnd ("g`g'_t`t1'") (`est') (`sev') (`pv')
    }
}
postclose hnd

csdid_estat simple
matrix rt = r(table)
local oest = el(rt, 1, 1)
local ose  = el(rt, 2, 1)
local op   = 2 * normal(-abs(`oest' / `ose'))
use gt_results, clear
local nn = _N + 1
set obs `nn'
replace term = "overall_simple" in `nn'
replace estimate = `oest' in `nn'
replace se = `ose' in `nn'
replace pvalue = `op' in `nn'
export delimited using "stata_results.csv", replace
exit, clear
