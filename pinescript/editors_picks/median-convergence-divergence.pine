// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © maksumit

//@version=5
indicator("Median Convergence Divergence", "MCD", timeframe="", timeframe_gaps=true)
//Inputs
fast = input.int(5, "Fast Length", 1)
slow = input.int(20, "Slow Length", 1)
src = input.source(close, "Source")
signal = input.int(10, "Signal Length", 1)

//Median, Median Convergence Divergence, Signal and Histogram
medianF = ta.median(src, fast)
medianS = ta.median(src, slow)
mcd = medianF - medianS
mcds = ta.median(mcd, signal)
hist = mcd - mcds

//Plots
plot(hist, "Histogram", style=plot.style_columns, color=hist<hist[1] and hist>0 ? color.green:hist>0 ? color.lime:hist>hist[1] ? color.maroon:color.red)
plot(mcds, "Signal Line", color=color.orange, linewidth=2)
plot(mcd, "MCD Line", color=color.blue, linewidth=2)
hline(0, "Zero Line")
