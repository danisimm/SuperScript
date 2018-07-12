import colour
import os
import pickle

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.ticker as mtick

base_path =  os.getcwd()

# set up color scheme
red = colour.Color("#B0413E")
yellow = colour.Color("#F9E884")
green = colour.Color("#709775")
units = 100
red_to_yellow = list(red.range_to(yellow,units))
yellow_to_green = list(yellow.range_to(green,10*units))
colours = red_to_yellow + yellow_to_green
colors = [i.hex for i in colours]
colors.extend(list(reversed(colors)))
included_frac = 99.
bin_percentiles = [(100-included_frac)/2.+i*(included_frac/len(colors)) for i in range(0,len(colors)+1)]
#add red bins for outside included_frac
colors = [red.hex] + colors + [red.hex]

testing = False

###########################################################################################################

def create_image(user_score, filename, time=0, percentage = False):
    output_filename = base_path + '/static/bars/' + filename + str(time) + '.png'
    ref_filename = base_path + '/static/references/'+ filename

    fig = pickle.load(open(ref_filename+'.pickle', 'rb'))
    bin_edges = pickle.load(open(ref_filename+'_bin_edges.pickle','rb'))

    ax = plt.gca()
    min,max = ax.get_xlim()
    

    #handle under/overflow
    if user_score < min + 0.025*(max-min):
        placement = min + 0.025*(max-min)
    elif user_score > max - 0.015*(max-min):
        placement = max- 0.015*(max-min)
    else:
        placement = user_score

    index = 0
    for i,edge in enumerate(bin_edges):
        if edge >= user_score:
            index = i
            break

    display_color = colors[index]

    

    if percentage:
        display_score = '{0:.1f}'.format(user_score)
        display_score = display_score + '%'
    else:
        display_score = '{0:.2f}'.format(user_score)


    el = Ellipse((2, -1), 0.5, 0.5)
    ax.add_patch(el)
    ann = ax.annotate(display_score,
                      xy=(placement, 1), xycoords='data',
                      xytext=(-40, 0), textcoords='offset points',
                      size=45, va="center",ha="left",
                      bbox=dict(boxstyle="round", fc=display_color, ec="k"),
                      arrowprops=dict(arrowstyle="wedge,tail_width=1.",
                                      fc=display_color, ec="k",
                                      patchA=None,
                                      patchB=el,
                                      relpos=(0, 0.5)))
    ax.tick_params(axis='x', which='major', pad=12)

    if percentage:
        fmt = '%.0f%%' # Format you want the ticks, e.g. '40%'
        xticks = mtick.FormatStrFormatter(fmt)
        ax.xaxis.set_major_formatter(xticks)

    extent = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    plt.savefig(output_filename, transparent=True,bbox_inches=extent.expanded(1.1, 2.5),dpi=800)

    plt.clf()