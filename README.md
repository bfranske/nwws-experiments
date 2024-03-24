This repositiory contains experiments for working with NWWS-OI (the NOAA Weather Wire Service Open Interface).

nwws.py - saves sample XML messages for a specific WFO (MPX is currently hard coded) into an output directory.

nwws-sqlog.py - saves WFO cccc codes which have transmitted a product to a sqlite database as well as full text of all products transmitted from a set of cccc codes (currently hard coded)