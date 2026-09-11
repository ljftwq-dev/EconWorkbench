.libPaths("D:/RLibrary")
library(did)
data(mpdta)
write.csv(mpdta, "mpdta_data.csv", row.names = FALSE)

# 官方金标准: group-time ATT + simple 聚合
out <- att_gt(yname = "lemp",
              tname = "year",
              idname = "countyreal",
              gname = "first.treat",
              xformla = ~1,
              data = mpdta,
              control_group = "nevertreated",
              bstrap = FALSE, clustervars = "countyreal")

# group-time ATT 表（只取 post 期，三软件对齐行集）
gt <- data.frame(group = out$group, t = out$t, att = out$att, se = out$se)
gt <- gt[gt$t >= gt$group, ]
gt$term <- paste0("g", gt$group, "_t", gt$t)
gt$pvalue <- 2 * pnorm(abs(gt$att / gt$se), lower.tail = FALSE)
res_gt <- data.frame(term = gt$term, estimate = gt$att, se = gt$se, pvalue = gt$pvalue)

agg <- aggte(out, type = "simple", bstrap = FALSE)
res_agg <- data.frame(term = "overall_simple", estimate = agg$overall.att,
                      se = agg$overall.se, pvalue = 2 * pnorm(abs(agg$overall.att / agg$overall.se), lower.tail = FALSE))

res <- rbind(res_gt, res_agg)
write.csv(res, "r_results.csv", row.names = FALSE)
cat("R done:", nrow(res), "rows; overall ATT =", round(agg$overall.att, 6), "SE =", round(agg$overall.se, 6), "\n")
