#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)

import argparse
import os

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gErrorIgnoreLevel = ROOT.kError


def main():
	
	parser = argparse.ArgumentParser(description="Print out the available LHE weights in a kappa skim (see also https://lhapdf.hepforge.org/pdfsets.html).", parents=[logger.loggingParser])
	parser.add_argument("file", help="Kappa skim output file")
	args = parser.parse_args()
	logger.initLogger(args)
	
	runs = ROOT.TChain("Runs")
	runs.Add(args.file)
	runs.GetEntry(0)
	
	lheWeightNamesMap = runs.runInfo.lheWeightNamesMap
	if len(lheWeightNamesMap) > 0:
		mapping = []
		for lheWeightNames in lheWeightNamesMap:
			mapping.append([lheWeightNames[0], lheWeightNames[1]])
	
		log.info("\nNames of available LHE weights (human readable:")
		for item in sorted(mapping, key=lambda item: item[0]):
			log.info("\t" + item[0])
	
		log.info("\nNames of available LHE weights (index):")
		for item in sorted(mapping, key=lambda item: int(item[1])):
			log.info("\t" + item[1])
	
		log.info("\nNames of available LHE weights (human readable -> index):")
		for item in sorted(mapping, key=lambda item: item[0]):
			log.info("\t" + item[0] + " -> " + item[1])
	
		log.info("\nNames of available LHE weights (index -> human readable):")
		for item in sorted(mapping, key=lambda item: int(item[1])):
			log.info("\t" + item[1] + " -> " + item[0])

	else:
		lumis = ROOT.TChain("Lumis")
		lumis.Add(args.file)
		lumis.GetEntry(0)
		
		lheWeightNames = lumis.genEventInfoMetadata.lheWeightNames
		log.info("\nIndices of available LHE weights:")
		for lheWeightName in lheWeightNames:
			log.info("\t" + lheWeightName)
		log.info("\nSee https://lhapdf.hepforge.org/pdfsets.html for more information")

if __name__ == "__main__":
	main()

