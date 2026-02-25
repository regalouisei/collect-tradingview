// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo

//@version=6
indicator("Clusters Volume Profile [LuxAlgo]", "LuxAlgo - Clusters Volume Profile", overlay = true, max_boxes_count = 500, max_labels_count = 500, max_lines_count = 500)

//---------------------------------------------------------------------------------------------------------------------}
// Constants & Palettes
//---------------------------------------------------------------------------------------------------------------------{
var color[] PALETTE = array.from(
     #2196f3, // Blue
     #f44336, // Red
     #4caf50, // Green
     #ff9800, // Orange
     #9c27b0, // Purple
     #00bcd4, // Cyan
     #ffeb3b, // Yellow
     #e91e63, // Pink
     #795548, // Brown
     #607d8b  // Blue Grey
 )

//---------------------------------------------------------------------------------------------------------------------}
// Inputs
//---------------------------------------------------------------------------------------------------------------------{
grp_main    = "Clustering Settings"
lookback    = input.int(200, "Lookback Period", minval = 10, group = grp_main, tooltip = "Number of recent bars to cluster and analyze.")
kInput      = input.int(5, "Number of Clusters", minval = 2, maxval = 10, group = grp_main, tooltip = "How many distinct price groups (clusters) to detect.")
iters       = input.int(50, "K-Means Iterations", minval = 5, maxval = 50, group = grp_main)

grp_vp      = "Volume Profile Settings"
rowsInput   = input.int(20, "Rows per Cluster VP", minval = 2, group = grp_vp, tooltip = "Number of histogram bins for each individual cluster's volume profile.")
vpWidth     = input.int(40, "Max VP Width (Bars)", minval = 5, group = grp_vp)
vpOffset    = input.int(10, "VP Offset", group = grp_vp)
showDots    = input.bool(true, "Highlight Price Dots", group = grp_vp, tooltip = "Limited by TradingView's label counts. Volume labels take priority.")
dotSizeInput = input.string(size.small, "Dot Size", options = [size.tiny, size.small, size.normal, size.large, size.huge], group = grp_vp)

//---------------------------------------------------------------------------------------------------------------------}
// K-Means & Logic
//---------------------------------------------------------------------------------------------------------------------{
f_kmeans(int n, int k, int iterations) =>
    float[] prices = array.new_float(0)
    float[] volumes = array.new_float(0)
    float minP = 1e10, maxP = -1e10
    
    for i = 0 to n - 1
        float p = hl2[i], v = volume[i]
        prices.push(p), volumes.push(v)
        minP := math.min(minP, p), maxP := math.max(maxP, p)
            
    float[] centroids = array.new_float(k)
    float step = (maxP - minP) / (k + 1)
    for i = 0 to k - 1
        centroids.set(i, minP + (i + 1) * step)
        
    int[] assignments = array.new_int(n)
    for iter = 1 to iterations
        for i = 0 to n - 1
            float p = prices.get(i)
            int best_k = 0
            float min_dist = 1e10
            for j = 0 to k - 1
                float dist = math.abs(p - centroids.get(j))
                if dist < min_dist
                    min_dist := dist, best_k := j
            assignments.set(i, best_k)
            
        float[] sum_pv = array.new_float(k, 0.0), sum_v = array.new_float(k, 0.0)
        for i = 0 to n - 1
            int cluster = assignments.get(i)
            sum_pv.set(cluster, sum_pv.get(cluster) + prices.get(i) * volumes.get(i))
            sum_v.set(cluster, sum_v.get(cluster) + volumes.get(i))
        for j = 0 to k - 1
            if sum_v.get(j) > 0
                centroids.set(j, sum_pv.get(j) / sum_v.get(j))
    
    [assignments, centroids]

//---------------------------------------------------------------------------------------------------------------------}
// Execution and Visuals
//---------------------------------------------------------------------------------------------------------------------{
var box[] allBoxes = array.new_box()
var label[] allLabels = array.new_label()
var line[] allLines = array.new_line()

if barstate.islast
    [assignments, centroids] = f_kmeans(lookback, kInput, iters)
    
    if allBoxes.size() > 0
        for b in allBoxes
            b.delete()
        allBoxes.clear()
    if allLabels.size() > 0
        for l in allLabels
            l.delete()
        allLabels.clear()
    if allLines.size() > 0
        for ln in allLines
            ln.delete()
        allLines.clear()

    int calcStart = bar_index - lookback + 1
    int vpStartX  = bar_index + vpOffset

    // Priority 1: Reserve labels for Volume Metrics (2 per cluster)
    int reservedForMetrics = kInput * 2
    int labelsUsed = 0

    for c_id = 0 to kInput - 1
        color clusterColor = PALETTE.get(c_id % PALETTE.size())
        
        float[] c_prices = array.new_float(0)
        float[] c_vols = array.new_float(0)
        float[] c_highs = array.new_float(0)
        float[] c_lows = array.new_float(0)
        
        float c_min = 1e10, c_max = -1e10
        float c_total_vol = 0.0
        
        // Data processing for cluster
        for i = 0 to lookback - 1
            if assignments.get(i) == c_id
                float p = hl2[i], v = volume[i], h = high[i], l = low[i]
                c_prices.push(p), c_vols.push(v), c_highs.push(h), c_lows.push(l)
                c_min := math.min(c_min, l), c_max := math.max(c_max, h)
                c_total_vol += v
                
                // Priority 2: Dot highlighting (if space permits)
                if showDots and labelsUsed < (500 - reservedForMetrics)
                    allLabels.push(label.new(bar_index - i, p, "•", 
                         color = #00000000, 
                         textcolor = clusterColor, 
                         style = label.style_label_center, 
                         size = dotSizeInput))
                    labelsUsed += 1

        if c_prices.size() > 0
            float[] binVols = array.new_float(rowsInput, 0.0)
            float binSize = (c_max - c_min) / rowsInput
            if binSize == 0
                binSize := syminfo.mintick
                
            for i = 0 to c_prices.size() - 1
                float b_h = c_highs.get(i), b_l = c_lows.get(i), b_v = c_vols.get(i)
                float wickRange = math.max(b_h - b_l, syminfo.mintick)
                for b_idx = 0 to rowsInput - 1
                    float binB = c_min + b_idx * binSize
                    float binT = binB + binSize
                    float intersectL = math.max(b_l, binB)
                    float intersectH = math.min(b_h, binT)
                    if intersectH > intersectL
                        binVols.set(b_idx, binVols.get(b_idx) + b_v * (intersectH - intersectL) / wickRange)
                
            float maxBinVol = binVols.max()
            int pocBinIdx = binVols.indexof(maxBinVol)
            
            for b_idx = 0 to rowsInput - 1
                if allBoxes.size() >= 500
                    break
                float vol = binVols.get(b_idx)
                if vol == 0
                    continue
                float b_bottom = c_min + b_idx * binSize
                float b_top = b_bottom + binSize
                int b_width = int((vol / maxBinVol) * vpWidth)
                int endX = vpStartX + b_width
                bool isPoc = b_idx == pocBinIdx
                color b_color = isPoc ? clusterColor : color.new(clusterColor, 75)
                
                allBoxes.push(box.new(vpStartX, b_top, endX, b_bottom, bgcolor = b_color, border_color = isPoc ? clusterColor : #00000000))
                     
                if isPoc
                    float pocY = (b_top + b_bottom) / 2
                    allLines.push(line.new(calcStart, pocY, vpStartX, pocY, color = clusterColor, width = 1, style = line.style_dashed))

                    // POC Volume Label
                    allLabels.push(label.new(calcStart, pocY, str.tostring(vol, format.volume), 
                         color = #00000000, textcolor = clusterColor, style = label.style_label_right, size = size.small))
                         
                    // Total Cluster Volume Label
                    allLabels.push(label.new(endX, pocY, "Total: " + str.tostring(c_total_vol, format.volume), 
                         color = #00000000, textcolor = clusterColor, style = label.style_label_left, size = size.small))

//---------------------------------------------------------------------------------------------------------------------}
