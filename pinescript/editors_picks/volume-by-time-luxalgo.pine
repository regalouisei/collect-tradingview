// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo

//@version=6
indicator("Volume by Time [LuxAlgo]", "LuxAlgo - Volume by Time", format = format.volume)

//---------------------------------------------------------------------------------------------------------------------}
//User Inputs
//---------------------------------------------------------------------------------------------------------------------{
avgType = input.string("Average", title = "Analysis Type", options = ["Average","Median"])
sz = input.int(0, title = "Length (Days)", tooltip = "Averaging Length\nSet Value to 0 for Max Analysis Length")
bidi = input.bool(false, title = "Bi-Directional", tooltip = "Enable Bi-Directional Display\nBearish Volume will be negative, Bullish Volume will be positive.")
upCol = input.color(#089981, title = "Bullish Color", group = "Style")
downCol = input.color(#f23645, title = "Bearish Color", group = "Style")
upVolCol = input.color(color.new(color.gray,60), title = "Up Volume Color", group = "Style")
downVolCol = input.color(color.new(color.black,60), title = "Down Volume Color", group = "Style")
invis = color.rgb(0,0,0,100)

//---------------------------------------------------------------------------------------------------------------------}
//UDTs
//---------------------------------------------------------------------------------------------------------------------{

type vols
    array<float> ary

//---------------------------------------------------------------------------------------------------------------------}
//Variables
//---------------------------------------------------------------------------------------------------------------------{

var data = map.new<int,vols>()

vol = volume
v = close > open  ? vol : -vol

hms = hour*10000 + minute*100 + second

//---------------------------------------------------------------------------------------------------------------------}
//Calculations
//---------------------------------------------------------------------------------------------------------------------{

if na(data.get(hms))
    data.put(hms,vols.new(array.from(float(vol))))
else
    if sz != 0 and data.get(hms).ary.size() == sz
        data.get(hms).ary.shift()
    data.get(hms).ary.push(v)

raw_avg = avgType == "Average" ? data.get(hms).ary.avg() : data.get(hms).ary.median()
avg = avgType == "Average" ? data.get(hms).ary.abs().avg() :  data.get(hms).ary.abs().median()

avg_col = raw_avg > 0 ? upCol : downCol
vol_col = close > open ? upVolCol : downVolCol
dir_avg = raw_avg > 0 ? avg : -avg

//---------------------------------------------------------------------------------------------------------------------}
//Display
//---------------------------------------------------------------------------------------------------------------------{

plotcandle(0,bidi?dir_avg:avg,0,bidi?dir_avg:avg, bordercolor = avg_col, color = invis, wickcolor = invis, title = "Average Volume", display = display.pane, editable = false)
plotcandle(0,bidi?v:vol,0,bidi?v:vol, bordercolor = vol_col, color = vol_col, wickcolor = invis, title = "Volume", display = display.pane, editable = false)

plot(vol, style = plot.style_columns, color = vol_col, title = "Volume", display = display.status_line, editable = false)
plot(avg, style = plot.style_columns, color = avg_col, title = "Average Volume", display = display.status_line, editable = false)

plot(data.get(hms).ary.size(), display = display.status_line, color = chart.fg_color, format = format.volume, title = "Avg Length Readout")

//---------------------------------------------------------------------------------------------------------------------}
