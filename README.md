# crn_paper
Scripts to generate results presented in, "Taming Randomness in Agent-Based Epidemiological Modeling using Common Random Numbers" by D. Klein, R. Abeysuriya, and C. Kerr. These examples leverage the Starsim agent-based modeling framework.

The three examples presented in the publication can be reproduced by running the following scripts:
* *PPH:* run_PPH.py
* *SIR:* run_SIR.py
* *VMMC:* run_VMMC.py

`pairwise_bias.py` was used to evaluate potential bias in pairwise random numbers, resulting in Appendix A.
`net_perf.py` was used to evaluate the performance of several networks, resulting in the figure in Appendix C.

The result of running each script is a corresponding folder of results and figures that will appear within the `figs` folder.

Other scripts here are for disease-specific modules like `hiv.py` and `PPH_demographics.py` or utilities like `plotting.py`.