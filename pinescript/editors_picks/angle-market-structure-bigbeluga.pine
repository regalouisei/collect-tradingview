// This work is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International  
// https://creativecommons.org/licenses/by-nc-sa/4.0/
// © BigBeluga

//@version=6
indicator("Angle Market Structure [BigBeluga]", overlay = true, max_lines_count = 500, max_labels_count = 500)

// ＩＮＰＵＴＳ ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――{

int   length            = input.int(5, "Length", group = "Angle MarketStructure")
float angle             = input.float(0.1, "Angle", step = 0.01, maxval = 1., minval = 0, inline = "1", group = "Angle MarketStructure")
color col1              = input.color(color.rgb(27, 202, 184), "", inline = "1", group = "Angle MarketStructure")
color col2              = input.color(color.rgb(203, 30, 122), "", inline = "1", group = "Angle MarketStructure")

float deviationSize     = input.float(1, "Deviation", step = 0.01, group = "Deviation")
string lbl_size         = input.string("normal", "Labels Size", ["tiny", "small", "normal", "large", "huge"], group = "Other")

size = switch lbl_size
    "tiny" => size.tiny
    "small" => size.small
    "normal" => size.normal
    "large" => size.large
    "huge" => size.huge

type deviation
    line  l1
    line  l2
    line  l3
    label lbl1 
    label lbl2 
    label lbl3

var dev = array.new<deviation>()
var phVal       = float(na)
var plVal       = float(na)
var upper       = line(na)
var upperLbl    = label(na)
var lower       = line(na)
var lowerLbl    = label(na)
// }


// ＣＡＬＣＵＬＡＴＩＯＮＳ――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――{

ph = ta.pivothigh(length, length)
pl = ta.pivotlow(length, length)

atr  = ta.atr(200) * angle
atr1 = ta.atr(200) * deviationSize

var countUp = 0
var countDn = 0

if not na(ph)
    phVal := high[length]
    upper := line.new(bar_index-length, ph, bar_index-length, ph, color = col1, width = 2)
if not na(pl)
    plVal := low[length]
    lower := line.new(bar_index-length, pl, bar_index-length, pl, color = col2, width = 2)

if na(ph)
    phVal -= atr
if na(pl)
    plVal += atr

if ta.crossover(high, phVal)
    countUp += 1
    upper.set_xy2(bar_index, phVal)
    upperLbl := label.new(upper.get_x1(), upper.get_y1(), str.tostring(countUp), color = color(na), textcolor = color.from_gradient(countUp, 0, 5, col1, chart.fg_color), size = size)
    countDn := 0

    //DeviationUP
    deviat = deviation.new(
         l1 = line.new(bar_index, phVal+atr1, bar_index, phVal+atr1, color = chart.fg_color),
         l2 = line.new(bar_index, phVal+atr1*2, bar_index, phVal+atr1*2, style = line.style_dashed, color = chart.fg_color),
         l3 = line.new(bar_index, phVal+atr1*3, bar_index, phVal+atr1*3, color = chart.fg_color),
         lbl1 = label.new(bar_index, phVal+atr1, "+1", style = label.style_label_left, textcolor = chart.fg_color, color = color(na), size = size),
         lbl2 = label.new(bar_index, phVal+atr1*2, "+2", style = label.style_label_left, textcolor  = chart.fg_color, color = color(na), size = size),
         lbl3 = label.new(bar_index, phVal+atr1*3, "+3", style = label.style_label_left, textcolor = chart.fg_color, color = color(na), size = size)
     )
    dev.push(deviat)
    phVal := float(na)

if ta.crossunder(low, plVal)
    countDn += 1
    lower.set_xy2(bar_index, plVal)
    countUp := 0
    lowerLbl := label.new(lower.get_x1(), lower.get_y1(), str.tostring(countDn), color = color(na), textcolor = color.from_gradient(countDn, 0, 5, col2, chart.fg_color), style = label.style_label_up, size = size)

    //DeviationDN
    deviat = deviation.new(
         l1 = line.new(bar_index, plVal-atr1, bar_index, plVal-atr1, color = chart.fg_color),
         l2 = line.new(bar_index, plVal-atr1*2, bar_index, plVal-atr1*2, style = line.style_dashed, color = chart.fg_color),
         l3 = line.new(bar_index, plVal-atr1*3, bar_index, plVal-atr1*3, color = chart.fg_color),
         lbl1 = label.new(bar_index, plVal-atr1, "-1", style = label.style_label_left, textcolor = chart.fg_color, color = color(na), size = size),
         lbl2 = label.new(bar_index, plVal-atr1*2, "-2", style = label.style_label_left, textcolor = chart.fg_color, color = color(na), size = size),
         lbl3 = label.new(bar_index, plVal-atr1*3, "-3", style = label.style_label_left, textcolor = chart.fg_color, color = color(na), size = size)
     )
    dev.push(deviat)
    plVal := float(na)

if dev.size() > 1
    d = dev.shift()

    d.l1.delete()
    d.l2.delete()
    d.l3.delete()
    d.lbl1.delete()
    d.lbl2.delete()
    d.lbl3.delete()

if dev.size() > 0

    for d in dev 
        d.l1.set_x2(bar_index+5)
        d.l2.set_x2(bar_index+5)
        d.l3.set_x2(bar_index+5)
        d.lbl1.set_x(bar_index+5)
        d.lbl2.set_x(bar_index+5)
        d.lbl3.set_x(bar_index+5)

plotshape(not na(ph) ? ph : na, "PivotHigh", shape.circle, location.absolute, offset = -length, color = color.new(col1, 80), size = size.small)
plotshape(not na(ph) ? ph : na, "PivotHigh", shape.circle, location.absolute, offset = -length, color = color.new(col1, 20), size = size.tiny)
plotshape(not na(pl) ? pl : na, "PivotLow", shape.circle, location.absolute, offset = -length, color = color.new(col2, 80), size = size.small)
plotshape(not na(pl) ? pl : na, "PivotLow", shape.circle, location.absolute, offset = -length, color = color.new(col2, 20), size = size.tiny)

// }
