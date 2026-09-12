# bp_r.R — strucchange::breakpoints reference implementation
# RSS is computed by hand from segment boundaries (bp$rss is NULL for ts objects).
# BUG-2 lesson: ts(start=..., frequency=12) assumes contiguous months; the series has
# gaps (missing January observations) -> dates must come from the real CSV column,
# never from the ts index. See README.
# .libPaths("D:/RLibrary")  # uncomment if strucchange lives in a user library
suppressMessages(library(strucchange))

d <- read.csv("rb_series.csv", stringsAsFactors = FALSE)
beta <- ts(d$beta, start = c(2012, 8), frequency = 12)  # positional carrier only

n <- length(beta)
h <- 24

rows <- list()
for (k in 0:4) {
  if (k == 0) {
    rss <- sum((beta - mean(beta))^2)
    nfound <- 0
    pos <- integer(0)
  } else {
    bp <- tryCatch(breakpoints(beta ~ 1, h = h, breaks = k), error = function(e) NULL)
    if (is.null(bp)) { cat("k =", k, "error, skip\n"); next }
    pos <- as.integer(bp$breakpoints)
    nfound <- length(pos)
    if (nfound == 0) { cat("k =", k, "no breaks returned, skip\n"); next }
    segs <- c(0, pos, n)
    rss <- 0
    for (s in seq_len(length(segs) - 1)) {
      seg <- beta[(segs[s] + 1):segs[s + 1]]
      rss <- rss + sum((seg - mean(seg))^2)
    }
  }
  bic <- n * log(rss / n) + ((k + 1) + k) * log(n)
  bstart <- if (nfound > 0) paste(d$date[pos + 1], collapse = ";") else ""
  rows[[length(rows) + 1]] <- data.frame(term = paste0("k=", k), estimate = rss,
                                         se = 0, pvalue = 0, breaks = bstart, bic = bic)
}
out <- do.call(rbind, rows)
write.csv(out, "r_results.csv", row.names = FALSE)
print(out)
cat("R done\n")
