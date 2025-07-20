I live in London, buy electricity and gas from Octopus Energy, and have a 5.5 kWp solar panel on my roof.
I ask:
* How much has the panel saved me?
* Is getting a battery worthwhile?

Via its API, Octopus Energy provides smart-meter data - including consumption of electricity and gas, and export of electricity - 
for 30-minute intervals. However, the questions above cannot be answered without _generation_ data. My panels come with SolisCloud app, 
which does not seem to allow any automatic data collection - please let me know if that is no longer the case - so I collect (daily)
data manually, and enter it in `data solis.csv`.

With Octopus and Solis datasets, I can calculate 
* how much I earned on exported electricity. (Well, Octopus already gives me this info in its app).
* how much I saved on un-imported electricity, i.e. electricity consumed out of own generation.   

Attached code 
* gets usage data from Octopus API, saving daily Parquet files to a subfolder
* combines Octopus and Solis data
* makes additional calculations
* saves output to CSV and Parquet files

You can use the code to fetch own Octopus usage data and, optionally, combine it with daily generation data from a different source. 
* Delete contents of `data octopus` folder. (Nah, I don't really care about sharing own energy-usage data with the world). 
* Get your Octopus account number, starting with A. 
* Sign up for Octopus developer account and obtain your API key.
* Enter the account number and the API key in `secrets SAMPLE.json`, renaming the file to `secrets.json`.
* Run script `1 get octopus_account_info.py`, after modifying `PATH`.
* Examine `octopus_account_info.json` and locate your meters' MPAN/MPRN codes and serial numbers.
* Modify API endpoint URLS - embedding the MPAN/MPRN codes and serial numbers - in `secrets.json`.   
* Modify `octopus_tariffs.json` to reflect your tariff history. 
* Run `2 get octopus usage data.py`, modifying `PATH` and the date range around line 13.
* Modify `data solis.csv`, recording generation data or zeroes.
* Run `3 process data.py`, after modifying `PATH`. The script will do daily calculations starting from the earliest date with Octopus data and ending with the earlier
of the latest date with Octopus data and the latest date with Solis data.  
* Examine `OUTPUT data octopus and solis wide.csv`

(Note: For me, `octopus_account_info.json` has two meters for both electricity and gas, although I have only one meter for each. I picked the right ones to use by trial and error).
