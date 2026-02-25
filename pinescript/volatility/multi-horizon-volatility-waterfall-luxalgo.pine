// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo

//@version=6
indicator("Multi-Horizon Volatility Waterfall [LuxAlgo]", "LuxAlgo - Volatility Waterfall", overlay = false)

//---------------------------------------------------------------------------------------------------------------------}
// Settings
//---------------------------------------------------------------------------------------------------------------------{
// Constants
color COLD_COLOR        = #2196f3
color HOT_COLOR         = #ff5252
color DATA              = #DBDBDB
color HEADERS           = #808080
color BACKGROUND        = #161616
color BORDERS           = #2E2E2E

string TOP_RIGHT        = 'Top Right'
string BOTTOM_RIGHT     = 'Bottom Right'
string BOTTOM_LEFT      = 'Bottom Left'

string TINY             = 'Tiny'
string SMALL            = 'Small'
string NORMAL           = 'Normal'
string LARGE            = 'Large'
string HUGE             = 'Huge'

// Groups
string G_MAIN           = "Main Settings"
string G_VIS            = "Visualization"
string G_DASH           = "Dashboard"

// Main Inputs
int   basePeriod        = input.int(10, "Base Horizon Step", minval = 5, group = G_MAIN)
int   rankPeriod        = input.int(200, "Percentile Lookback", minval = 50, group = G_MAIN)
int   smoothInput       = input.int(5, "Smoothing", minval = 1, group = G_MAIN)

// Visual Inputs
color coldColorInput    = input.color(COLD_COLOR, "Cold (Low Vol)", group = G_VIS, inline = "colors")
color hotColorInput     = input.color(HOT_COLOR, "Hot (High Vol)", group = G_VIS, inline = "colors")
bool  colorBarsInput    = input.bool(true, "Color Candles by Volatility Heat", group = G_VIS)
int   maxGlowIntensity  = input.int(35, "Max Glow Intensity (%)", minval = 1, maxval = 100, group = G_VIS, tooltip = "Controls the maximum brightness of the expansion glow on the main chart.")

// Dashboard Inputs
bool   dashInput        = input.bool(true, "Show Dashboard", group = G_DASH)
string dashPosInput     = input.string(TOP_RIGHT, "Position", group = G_DASH, options = [TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT])
string dashSizeInput    = input.string(SMALL, "Size", group = G_DASH, options = [TINY, SMALL, NORMAL, LARGE, HUGE])

//---------------------------------------------------------------------------------------------------------------------}
// Functions / Methods
//---------------------------------------------------------------------------------------------------------------------{
// @function Calculate Normalized Volatility Heat
get_vol_heat(int length, int rank, int smooth) =>
    float vol = ta.atr(length) / close
    float rankVal = ta.percentrank(vol, rank)
    ta.ema(rankVal, smooth)

// @function Dashboard Cell Helper
var parsedDashSize = switch dashSizeInput
    TINY   => size.tiny
    SMALL  => size.small
    NORMAL => size.normal
    LARGE  => size.large
    HUGE   => size.huge

var parsedDashPos = switch dashPosInput
    TOP_RIGHT    => position.top_right
    BOTTOM_RIGHT => position.bottom_right
    BOTTOM_LEFT  => position.bottom_left

cell(table t, int col, int row, string txt, color c = #FFFFFF, align = text.align_right, color bg = na, float h = 0) => 
    t.cell(col, row, txt, text_color = c, text_size = parsedDashSize, text_halign = align, bgcolor = bg, height = h)

divider(table t, int row, int lastCol) =>    
    t.merge_cells(0, row, lastCol, row)
    cell(t, 0, row, '━━━━━━━━━━━━━━', align = text.align_center, h = 0.5, c = BORDERS)

//---------------------------------------------------------------------------------------------------------------------}
// Calculations
//---------------------------------------------------------------------------------------------------------------------{
float h1  = get_vol_heat(basePeriod * 1,  rankPeriod, smoothInput)
float h2  = get_vol_heat(basePeriod * 2,  rankPeriod, smoothInput)
float h3  = get_vol_heat(basePeriod * 3,  rankPeriod, smoothInput)
float h4  = get_vol_heat(basePeriod * 4,  rankPeriod, smoothInput)
float h5  = get_vol_heat(basePeriod * 5,  rankPeriod, smoothInput)
float h6  = get_vol_heat(basePeriod * 6,  rankPeriod, smoothInput)
float h7  = get_vol_heat(basePeriod * 7,  rankPeriod, smoothInput)
float h8  = get_vol_heat(basePeriod * 8,  rankPeriod, smoothInput)
float h9  = get_vol_heat(basePeriod * 9,  rankPeriod, smoothInput)
float h10 = get_vol_heat(basePeriod * 10, rankPeriod, smoothInput)

float aggHeat = (h1 + h2 + h3 + h4 + h5 + h6 + h7 + h8 + h9 + h10) / 10
color heatCol = color.from_gradient(aggHeat, 0, 100, coldColorInput, hotColorInput)

//---------------------------------------------------------------------------------------------------------------------}
// Visuals
//---------------------------------------------------------------------------------------------------------------------{
// 1. Candle Coloring (Still applies to main chart even from separate pane)
barcolor(colorBarsInput ? heatCol : na, title = "Waterfall Candle Heat")

// 2. Waterfall Ribbon Design (In separate pane)
plot_h1  = plot(10, "H1", display = display.none)
plot_h2  = plot(9,  "H2", display = display.none)
plot_h3  = plot(8,  "H3", display = display.none)
plot_h4  = plot(7,  "H4", display = display.none)
plot_h5  = plot(6,  "H5", display = display.none)
plot_h6  = plot(5,  "H6", display = display.none)
plot_h7  = plot(4,  "H7", display = display.none)
plot_h8  = plot(3,  "H8", display = display.none)
plot_h9  = plot(2,  "H9", display = display.none)
plot_h10 = plot(1,  "H10", display = display.none)

fill(plot_h1, plot_h2, color.from_gradient(h1, 0, 100, coldColorInput, hotColorInput), "Fill H1-H2")
fill(plot_h2, plot_h3, color.from_gradient(h2, 0, 100, coldColorInput, hotColorInput), "Fill H2-H3")
fill(plot_h3, plot_h4, color.from_gradient(h3, 0, 100, coldColorInput, hotColorInput), "Fill H3-H4")
fill(plot_h4, plot_h5, color.from_gradient(h4, 0, 100, coldColorInput, hotColorInput), "Fill H4-H5")
fill(plot_h5, plot_h6, color.from_gradient(h5, 0, 100, coldColorInput, hotColorInput), "Fill H5-H6")
fill(plot_h6, plot_h7, color.from_gradient(h6, 0, 100, coldColorInput, hotColorInput), "Fill H6-H7")
fill(plot_h7, plot_h8, color.from_gradient(h7, 0, 100, coldColorInput, hotColorInput), "Fill H7-H8")
fill(plot_h8, plot_h9, color.from_gradient(h8, 0, 100, coldColorInput, hotColorInput), "Fill H8-H9")
fill(plot_h9, plot_h10, color.from_gradient(h9, 0, 100, coldColorInput, hotColorInput), "Fill H9-H10")

// 3. Aggregate Heat Line
plot(aggHeat / 10, "Aggregate Vol Line", color = color.new(chart.fg_color, 50), linewidth = 2)

// 4. Dashboard
if barstate.islast and dashInput
    var table t = table.new(parsedDashPos, 2, 7, bgcolor = BACKGROUND, frame_color = BORDERS, frame_width = 1, force_overlay = true)
    
    t.merge_cells(0, 0, 1, 0)
    cell(t, 0, 0, 'Volatility Waterfall', c = DATA, align = text.align_center)
    divider(t, 1, 1)
    
    cell(t, 0, 2, 'Aggregate Heat', c = HEADERS, align = text.align_left)
    cell(t, 1, 2, str.format("{0,number,#.##}%", aggHeat), c = heatCol)
    
    divider(t, 3, 1)
    
    cell(t, 0, 4, 'Regime', c = HEADERS, align = text.align_left)
    cell(t, 1, 4, aggHeat > 70 ? 'Expansion' : aggHeat < 30 ? 'Compression' : 'Neutral', c = heatCol)
    
    divider(t, 5, 1)
    
    cell(t, 0, 6, 'Fast/Slow Ratio', c = HEADERS, align = text.align_left)
    cell(t, 1, 6, str.format("{0,number,#.##}", h1 / h10), c = DATA)

// Labels for Clarity (In indicator pane)
if barstate.islast
    label.new(bar_index + 2, 10, "Fast Vol", color = #00000000, textcolor = chart.fg_color, style = label.style_label_left, size = size.small)
    label.new(bar_index + 2, 1, "Slow Vol", color = #00000000, textcolor = chart.fg_color, style = label.style_label_left, size = size.small)

// Background Glow (Main Chart)
// The transparency now "fades" dynamically and respects the user-defined Max Glow Intensity
float intensity = aggHeat > 70 ? (aggHeat - 70) / 30 : 0
float currentOpacity = intensity * maxGlowIntensity
bgcolor(aggHeat > 70 ? color.new(hotColorInput, 100 - currentOpacity) : na, title = "Expansion Glow", force_overlay = true)

//---------------------------------------------------------------------------------------------------------------------}
