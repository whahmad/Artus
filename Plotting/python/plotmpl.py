#  -*- coding: utf-8 -*-

"""
"""
import os
import logging
import HarryPlotter.Utility.logger as logger
log = logging.getLogger(__name__)

import ROOT

import HarryPlotter.Plotting.plotbase as plotbase
import HarryPlotter.Utility.mplconvert as mplconvert

import HarryPlotter.Utility.rootpy

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.colors import Normalize
import matplotlib.gridspec as gridspec

import numpy as np

class PlotMpl(plotbase.PlotBase):
	def __init__(self):
		super(PlotMpl, self).__init__()
		self.mpl_version = int(matplotlib.__version__.replace(".", ""))
		self.set_matplotlib_defaults()

	def modify_argument_parser(self, parser, args):
		super(PlotMpl, self).modify_argument_parser(parser, args)
		self.formatting_options.add_argument("--colormap", default="afmhot", nargs="?",
		                                     help="Colormap for matplotlib [Default: 'afmhot']")
	def prepare_args(self, parser, plotData):
		super(PlotMpl, self).prepare_args(parser, plotData)

		# Set meaningful default values for colors if none provided
		default_colorcycle = iter(matplotlib.rcParams['axes.color_cycle'])
		for index, color in enumerate(plotData.plotdict["colors"]):
			if color is None:
				plotData.plotdict["colors"][index] = next(self._default_colorcycle)
			else:
				plotData.plotdict["colors"][index] = color
		self.set_default_ratio_colors(plotData)
		
		# defaults for markers
		for index, marker in enumerate(plotData.plotdict["markers"]):
			if marker == None:
				plotData.plotdict["markers"][index] = "-"

		# default for linestyles
		for index, linestyle in enumerate(plotData.plotdict["linestyles"]):
			if linestyle == None:
				plotData.plotdict["linestyles"][index] = "-"

	def run(self, plotData):
		super(PlotMpl, self).run(plotData)
	
	def create_canvas(self, plotData):
		if plotData.plotdict["ratio"]:
			self.fig = plt.figure()
			self.ax = plt.subplot2grid((4,1), (0, 0), rowspan=3)
			self.ax2 = plt.subplot2grid((4,1), (3, 0))
			#plotdict['ratiosubplotaxes'] = ax2 # needed?
		else:
			self.fig = plt.figure()
			self.ax = self.fig.add_subplot(111)


		if plotData.plotdict["x_lims"] is not None:
			self.ax.set_xlim([plotData.plotdict["x_lims"][0],plotData.plotdict["x_lims"][1]])
		if plotData.plotdict["y_lims"] is not None:
			self.ax.set_ylim(plotData.plotdict["y_lims"][0],plotData.plotdict["y_lims"][1])

		if plotData.plotdict["ratio"] and plotData.plotdict["y_ratio_lims"] != None:
			self.ax2.set_ylim(plotData.plotdict["y_ratio_lims"][0],plotData.plotdict["y_ratio_lims"][1])

	def prepare_histograms(self, plotData):
		self.bottom_y_values = {}


	def make_plots(self, plotData):
		# validate length of parameters first
		zip_arguments = ( list(set(plotData.plotdict["nicks"])),
		                                 plotData.plotdict["colors"],
		                                 plotData.plotdict["labels"],
		                                 plotData.plotdict["markers"],
		                                 plotData.plotdict["errorbars"],
		                                 plotData.plotdict["linestyles"])
		for argument in zip_arguments:
			if len(argument) != len(zip_arguments[0]):
				log.warning("The PlotMpl module is trying to make plots with invalid inputs. The Plot will eventually not contain all requested information.")
				break

		for nick, color, label, marker, errorbar, linestyle in zip(*zip_arguments):
			root_object = plotData.plotdict["root_objects"][nick]
			if isinstance(root_object, ROOT.TGraph):
				mpl_histogram = mplconvert.root2histo(root_object, "someFilename", 1)
				self.plot1D = isinstance(mpl_histogram, mplconvert.Histo)
				self.plot2D = isinstance(mpl_histogram, mplconvert.Histo2D)
				yerr=mpl_histogram.yerr if errorbar else None
				y = np.array(mpl_histogram.y)
				self.ax.errorbar(mpl_histogram.xc, y, yerr=yerr,
				                 color=color, fmt=marker, capsize=0, label=label, zorder=10, drawstyle='steps-mid', linestyle=linestyle)

			elif isinstance(root_object, ROOT.TH1):
				mpl_histogram = mplconvert.root2histo(root_object, "someFilename", 1)
				self.plot1D = isinstance(mpl_histogram, mplconvert.Histo)
				self.plot2D = isinstance(mpl_histogram, mplconvert.Histo2D)

				# determine bin width to allow variable binning
				widths = np.array([root_object.GetXaxis().GetBinWidth(i) for i in xrange(1,root_object.GetNbinsX()+1)])
				# all bin edges of histogram without over/underflow bins
				bin_edges = np.array(mpl_histogram.x + [mpl_histogram.xc[-1] + mpl_histogram.xerr[-1]])
				yerr=mpl_histogram.yerr if errorbar else None

				if self.plot2D:
					norm = LogNorm if plotData.plotdict["z_log"] else Normalize
					self.image = self.ax.imshow(mpl_histogram.BinContents,
					                            interpolation='nearest',
					                            origin='lower',
					                            extent=[mpl_histogram.xborderlow, mpl_histogram.xborderhigh, mpl_histogram.yborderlow, mpl_histogram.yborderhigh],
					                            aspect='auto',
					                            cmap=plt.cm.get_cmap(plotData.plotdict["colormap"]),
					                            norm=norm())
				elif marker=="bar":
					bottom=0.
					self.ax.bar(mpl_histogram.x, mpl_histogram.y, widths, yerr=yerr, bottom=bottom,
					            label=label, fill=True, facecolor=color, edgecolor=color, ecolor=color, alpha=1.0)
				elif marker=='fill':
					y = np.array(mpl_histogram.y)
					self.ax.fill_between(x=self.steppify_bin(bin_edges, isx=True), y1=self.steppify_bin(y),y2=0., color=color,
					                     facecolor=color, edgecolor=color, alpha=1.0, zorder=1)
					if errorbar:
						self.ax.errorbar(mpl_histogram.xc, y, yerr=yerr,
						                 color=color, fmt='+', capsize=0, zorder=1, linestyle='')
					# draw the legend proxy
					proxy = plt.Rectangle((0, 0), 0, 0, label=label, facecolor=color, edgecolor='black', alpha=1.0)
					self.ax.add_patch(proxy)
				else:
					y = np.array(mpl_histogram.y)
					self.ax.plot(self.steppify_bin(bin_edges, isx=True), self.steppify_bin(y), color=color,
					             linestyle='-', label=label, zorder = 4)
					if errorbar:
						self.ax.errorbar(mpl_histogram.xc, y, yerr=yerr,
						                 color=color, fmt=marker, capsize=0, zorder=4, linestyle='')
			# draw functions from dictionary
			elif isinstance(root_object, ROOT.TF1):
				x_values = []
				y_values = []
				sampling_points = 1000
				x_range = [ root_object.GetXaxis().GetXmin(), root_object.GetXaxis().GetXmax()] 
				for x in np.arange(x_range[0], x_range[1], (float(x_range[1])-float(x_range[0]))/sampling_points):
					x_values.append(x)
					y_values.append(root_object.Eval(x))
				self.ax.plot(x_values, y_values, label=label, color=color, linestyle=linestyle, linewidth=2)

		if plotData.plotdict["ratio"]:
			for root_object, ratio_color, ratio_marker, in zip(plotData.plotdict["root_ratio_histos"],
				                                               plotData.plotdict["ratio_colors"],
				                                               plotData.plotdict["ratio_markers"]):
				mpl_histogram = mplconvert.root2histo(root_object)
				self.ax2.axhline(1.0, color='black')
				self.ax2.errorbar(mpl_histogram.xc, mpl_histogram.y, mpl_histogram.yerr, ecolor=ratio_color, fmt=ratio_marker)



	def modify_axes(self, plotData):
		# do what is needed for all plots:
		super(PlotMpl, self).modify_axes(plotData)

		self.ax.grid(plotData.plotdict["grid"])

		if not plotData.plotdict["ratio"]:
			self.ax.set_xlabel(plotData.plotdict["x_label"], position=(1., 0.), va='top', ha='right')
		self.ax.set_ylabel(plotData.plotdict["y_label"], position=(0., 1.), va='top', ha='right')
		# self.ax.ticklabel_format(style='sci',scilimits=(-3,4),axis='both')

		# do special things for 1D Plots
		if self.plot1D:
			if plotData.plotdict["x_log"]: 
				self.ax.set_xscale('log', nonposx='clip')
			if plotData.plotdict["y_log"]: 
				self.ax.set_yscale('log', nonposy='clip')

			if plotData.plotdict["ratio"]:
				self.ax2.set_xlabel(plotData.plotdict["x_label"],position=(1., 0.), va='top', ha='right')
				self.ax2.set_ylabel(plotData.plotdict["y_ratio_label"])
				self.ax2.grid(plotData.plotdict["ratio_grid"])
				# Don't show ticklabels on main plot
				self.ax.xaxis.set_ticklabels([])
				# Ratio plot shares xlims of main plot
				self.ax2.set_xlim(self.ax.get_xlim())
				if plotData.plotdict["x_log"]: 
					self.ax2.set_xscale('log', nonposx='clip')

		# do special things for 2D Plots
		if self.plot2D:
			cb = self.fig.colorbar(self.image, ax=self.ax)


	def add_labels(self, plotData):
		super(PlotMpl, self).add_labels(plotData)

		if plotData.plotdict["title"]:
			self.ax.set_title(plotData.plotdict["title"], fontsize=14)

		if not (plotData.plotdict["lumi"]==None):
			plt.text(-0.0, 1.030, "$\mathcal{L}=" + str(plotData.plotdict["lumi"]) + "\mathrm{fb^{-1}}$", transform=self.ax.transAxes, fontsize=10)
			#self.fig.suptitle("$\mathcal{L}=" + str(plotData.plotdict["lumi"]) + "\mathrm{fb^{-1}}$", ha="center", x=0.4)
		if not (plotData.plotdict["energy"] == None):
			energy = "+".join(plotData.plotdict["energy"])
			plt.text(1.0, 1.030, "$\sqrt{s}=" + energy + "\\ \mathrm{TeV}$", transform=self.ax.transAxes, fontsize=10, horizontalalignment="right")
			#self.fig.suptitle("$\sqrt{s}=" + energy + "\\ \mathrm{TeV}$", ha="right",x=0.9) 
		legend = self.ax.legend(loc='upper right')
		if self.mpl_version >= 121:
			plt.tight_layout()
		# Decrease vertical distance between subplots
		plt.subplots_adjust(hspace=0.2)

	def save_canvas(self, plotData):
		for output_filename in plotData.plotdict["output_filenames"]:
			self.fig.savefig(output_filename)
			log.info("Created plot \"%s\"." % output_filename)

	@staticmethod
	def set_matplotlib_defaults():
		# Set matplotlib rc settings
		# matplotlib.rcParams['font.family'] = 'sans-serif'
		matplotlib.rcParams['mathtext.fontset'] = 'stixsans'
		matplotlib.rcParams['mathtext.default'] = 'rm'
		# matplotlib.rcParams['font.sans-serif'] = 'helvetica, Helvetica, Nimbus Sans L, Mukti Narrow, FreeSans'
		# figure
		matplotlib.rcParams['figure.figsize'] = 7., 7.
		# axes
		matplotlib.rcParams['axes.linewidth'] = 2
		matplotlib.rcParams['axes.labelsize'] = 20
		matplotlib.rcParams['xtick.labelsize'] = 16
		matplotlib.rcParams['xtick.major.size'] = 12
		matplotlib.rcParams['xtick.minor.size'] = 6
		matplotlib.rcParams['ytick.labelsize'] = 16
		matplotlib.rcParams['ytick.major.size'] = 14
		matplotlib.rcParams['ytick.minor.size'] = 7
		matplotlib.rcParams['lines.markersize'] = 8
		# color cycle
		matplotlib.rcParams['axes.color_cycle'] = [(0.0, 0.0, 0.0),
		                                           (0.21568627450980393, 0.49411764705882355, 0.7215686274509804),
		                                           (0.30196078431372547, 0.6862745098039216, 0.2901960784313726),
		                                           (0.596078431372549, 0.3058823529411765, 0.6392156862745098),
		                                           (1.0, 0.4980392156862745, 0.0),
		                                           (1.0, 1.0, 0.2),
		                                           (0.6509803921568628, 0.33725490196078434, 0.1568627450980392),
		                                           (0.9686274509803922, 0.5058823529411764, 0.7490196078431373),
		                                           (0.6, 0.6, 0.6)]
		# legend
		matplotlib.rcParams['legend.numpoints'] = 1
		matplotlib.rcParams['legend.fontsize'] = 19
		matplotlib.rcParams['legend.labelspacing'] = 0.3
		matplotlib.rcParams['legend.frameon'] = False
		  # Saving
		matplotlib.rcParams['savefig.bbox'] = 'tight'
		matplotlib.rcParams['savefig.dpi'] = 150
		matplotlib.rcParams['savefig.format'] = 'png'
		matplotlib.rcParams['agg.path.chunksize'] = 20000


	@staticmethod
	def steppify_bin(arr, isx=False):
		"""
		Produce stepped array of arr, also of x
		"""
		if isx:
			newarr = np.array(zip(arr[:-1], arr[1:])).ravel()
		else:
			newarr = np.array(zip(arr, arr)).ravel()
		return newarr

	def plot_errorbar(hist, xerr=True, yerr=True, emptybins=True, ax=None, zorder=1, **kwargs)
	
		if ax is None:
			ax = plt.gca()
		pass

		if xerr:
			xerr = np.array(h.xerrl, h.xerrh)
		else:
			xerr = 0.
		if yerr:
			yerr = np.array(h.yerrl, h.yerrh)
		else:
			yerr = 0.

		ax.errorbar(h.x, h.y, xerr=xerr, yerr=yerr, zorder=zorder, **kwargs)

	def plot_hist1d(hist, style='fill', **kwargs):

		if ax is None:
			ax = plt.gca()
		pass

		bottom = 0.
		x = self.steppify_bin(hist.xedges, isx=True)
		y = self.steppify_bin(hist.y)

		ax.fill_between(x, y, bottom=0., color=color,
		                alpha=1.0, zorder=1)
		# draw the legend proxy
		proxy = plt.Rectangle((0, 0), 0, 0, label=label, facecolor=color, edgecolor='black', alpha=1.0)
		self.ax.add_patch(proxy)
