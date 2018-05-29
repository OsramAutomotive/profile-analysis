import matplotlib.pyplot as plt
from matplotlib import style
import re


def plot_profile_matplotlib(upper_threshold, lower_threshold, tolerance, rate_adjustment, 
                            title, df_plot, channels, tc_channel_names, regex_temp):
    fig, ax = set_up_plot_area(title)
    ax.plot(df_plot.index.to_pydatetime(), df_plot[channels], linewidth=1.5)
    ax.set_ylabel("Temperature (°C)")
    ax.set_xlabel("Date Time")
    tol = tolerance if tolerance else 0
    tc_labels = [re.search(regex_temp, channel).group(0)+' '+name for channel, name in tc_channel_names.items()]
    ax.axhline(y=upper_threshold-tol, color='k', linestyle='--', linewidth=2, alpha=0.6)
    ax.axhline(y=lower_threshold+tol, color='k', linestyle='--', linewidth=2, alpha=0.6)
    if rate_adjustment: 
        adjustment = (upper_threshold - lower_threshold) * rate_adjustment / 100
        ax.axhline(y=upper_threshold-adjustment, color='k', linestyle=':', linewidth=2, alpha=0.5)
        ax.axhline(y=lower_threshold+adjustment, color='k', linestyle=':', linewidth=2, alpha=0.5)
    ax.legend(labels=sorted(tc_labels), 
              bbox_to_anchor=(0., 1.02, 1., .102), loc=3, 
              mode="expand", borderaxespad=0., ncol=5)
    plt.tight_layout()
    fig.subplots_adjust(top=0.82, bottom=0.07)

def set_up_plot_area(title, pstyle='ggplot'):
    style.use(pstyle)  ## set formatting style to use for matplotlib
    fig, ax = plt.subplots(sharex=True)
    fig.suptitle(title, fontsize = 20, fontweight= 'bold')  ## main title for entire figure
    return fig, ax
